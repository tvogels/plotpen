import json
from matplotlib import pyplot as plt
from io import BytesIO
from matplotlib.lines import Line2D
from xml.etree import ElementTree

results = {}
for marker, name in Line2D.markers.items():
    if name == "nothing":
        continue
    print(name, marker)
    plt.plot(0, 0, marker=marker)
    plt.gca().axis("off")
    buffer= BytesIO()
    plt.savefig(buffer, format="svg")
    plt.close()
    buffer.seek(0)
    tree = ElementTree.parse(buffer)
    elems = tree.findall(".//{http://www.w3.org/2000/svg}path")

    markerkey = str(marker)
    results[markerkey] = {"marker": marker, "name": name, "d": elems[2].attrib["d"]}

    # print(ElementTree.tostring(tree.getroot()).decode('ascii'))

    with open("markers.json", "w") as fp:
        json.dump(results, fp, indent=1)