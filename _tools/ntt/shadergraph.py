"""Scene materials (.MATERIAL): the editor shader graph embedded as XML.

    <materialInstance name=...>
      <shaderNodeInstance name=... shaderNodeRef="sampleTexture2D|mul|lerp|parameter3|Mesh Colour|...">
        <userParam|userValue name="tex|A|..." value=... />
      </shaderNodeInstance>
      <link nodeFrom socketFrom nodeTo socketTo />
    </materialInstance>

The graph ends in a StandardMaterial node (sockets Albedo, Alpha, Normal, Roughness,
Metalness, Emissive, AO Factor ...). `evaluate` walks back from those sockets and
approximates each input as (texture, uv set, constant colour, uses vertex colour) so it can
be expressed as a glTF PBR material. Blends that add weathering (lerp B inputs such as sand)
are dropped in favour of the base (lerp A) input.
"""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from .resource import parse_resource

OUTPUT_NODES = ("StandardMaterial",)


@dataclass
class Input:
    texture: str | None = None
    texcoord: int = 0
    channel: str = "RGB"
    color: tuple | None = None     # constant multiplier (linear-ish authored values)
    vertex_color: bool = False

    def empty(self):
        return self.texture is None and self.color is None and not self.vertex_color


@dataclass
class Graph:
    name: str
    nodes: dict                    # name -> (ref, params)
    links: dict                    # (nodeTo, socketTo) -> (nodeFrom, socketFrom)
    inputs: dict = field(default_factory=dict)   # nodeTo -> [(socketTo, nodeFrom, socketFrom)]


def _floats(text):
    text = re.sub(r"^\s*float\d\s*\(", "(", text or "")
    return tuple(float(x) for x in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", text))


def parse_graph(data: bytes) -> Graph | None:
    i, j = data.find(b"<materialInstance"), data.find(b"</materialInstance>")
    if i < 0 or j < 0:
        return None
    root = ET.fromstring(data[i:j + len(b"</materialInstance>")].decode("latin-1"))
    nodes, links, inputs = {}, {}, {}
    for n in root.findall("shaderNodeInstance"):
        params = {p.get("name"): p.get("value") for p in n if p.tag in ("userParam", "userValue")}
        nodes[n.get("name")] = (n.get("shaderNodeRef"), params)
    for l in root.findall("link"):
        key = (l.get("nodeTo"), l.get("socketTo"))
        links[key] = (l.get("nodeFrom"), l.get("socketFrom"))
        inputs.setdefault(l.get("nodeTo"), []).append((l.get("socketTo"), l.get("nodeFrom"), l.get("socketFrom")))
    return Graph(root.get("name", ""), nodes, links, inputs)


def _merge(a: Input, b: Input) -> Input:
    """Product of two inputs."""
    out = Input(a.texture or b.texture, a.texcoord if a.texture else b.texcoord,
                a.channel if a.texture else b.channel, None, a.vertex_color or b.vertex_color)
    if a.color and b.color:
        n = max(len(a.color), len(b.color))
        ac = a.color * n if len(a.color) == 1 else a.color
        bc = b.color * n if len(b.color) == 1 else b.color
        out.color = tuple(x * y for x, y in zip(ac, bc))
    else:
        out.color = a.color or b.color
    return out


def _eval(g: Graph, node: str, socket: str, depth=0) -> Input:
    if depth > 24 or node not in g.nodes:
        return Input()
    ref, params = g.nodes[node]
    ins = {s: (n, fs) for s, n, fs in g.inputs.get(node, [])}

    def sub(sock):
        if sock in ins:
            return _eval(g, ins[sock][0], ins[sock][1], depth + 1)
        return Input()

    if ref == "sampleTexture2D":
        uv = 0
        if "UV" in ins:
            src_ref = g.nodes.get(ins["UV"][0], ("", {}))[0]
            m = re.search(r"_(\d+)$", ins["UV"][0])
            if src_ref == "Mesh UV" and m and ins["UV"][0] != "Mesh UV_0":
                uv = int(m.group(1))
        return Input(params.get("tex"), uv, socket or "RGB")
    if ref == "Mesh Colour":
        return Input(vertex_color=True)
    if ref and re.match(r"(instanced_)?(parameter|constant)[1-4]$", ref):
        vals = _floats(params.get("A"))
        return Input(color=vals) if vals else Input()
    if ref in ("float2", "float3"):
        return Input()
    if ref == "mul":
        return _merge(sub("A"), sub("B"))
    if ref == "lerp":
        a = sub("A")
        return a if not a.empty() else sub("B")
    if ref == "Expand NormalR":
        return sub("NormalR")
    if ref in ("Time", "Camera Transform", "Object Transform", "Screen UV", "fresnel", "distance", "sin"):
        return Input()
    # anything else: pass the main signal through (e.g. Shader Mode's Normal branch, Desaturate's
    # Input, Remap, Over ...), ignoring scalar controls such as Amount/Strength
    order = sorted(g.inputs.get(node, []), key=lambda t: (t[0] not in MAIN_SOCKETS, MAIN_SOCKETS.index(t[0])
                                                           if t[0] in MAIN_SOCKETS else 0))
    fallback = Input()
    for s, n, fs in order:
        got = _eval(g, n, fs, depth + 1)
        if got.texture or got.vertex_color or (got.color and len(got.color) >= 3):
            return got
        if fallback.empty() and not got.empty():
            fallback = got
    return fallback


MAIN_SOCKETS = ("Normal", "Input", "A", "RGB", "Colour", "Color", "In", "Base", "B")


@dataclass
class SceneMaterial:
    name: str
    albedo: Input
    alpha: Input
    normal: Input
    roughness: Input
    emissive: Input
    metalness: Input
    alpha_linked: bool


def read_material(path: str) -> SceneMaterial | None:
    with open(path, "rb") as f:
        raw = f.read()
    try:
        data = parse_resource(raw, path).body
    except Exception:
        data = raw
    g = parse_graph(data)
    if g is None:
        return None
    out = next((n for n, (ref, _) in g.nodes.items() if ref in OUTPUT_NODES), None)

    def sock(name):
        if out is None or (out, name) not in g.links:
            return Input()
        n, s = g.links[(out, name)]
        return _eval(g, n, s)

    return SceneMaterial(g.name, sock("Albedo"), sock("Alpha"), sock("Normal"), sock("Roughness"),
                         sock("Emissive"), sock("Metalness"), out is not None and (out, "Alpha") in g.links)
