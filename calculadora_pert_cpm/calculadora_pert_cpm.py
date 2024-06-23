import js
from pyodide.ffi import create_proxy
import micropip


async def load_packages():
    await micropip.install("matplotlib")
    await micropip.install("networkx")
    await micropip.install("pillow")


async def get_activity_data(event):
    await load_packages()
    num_activities = int(js.document.getElementById("num_activities").value)
    activities_input_div = js.document.getElementById("activities_input")
    activities_input_div.innerHTML = ""

    table = js.document.createElement("table")
    table.setAttribute("id", "activities_table")

    header = js.document.createElement("tr")
    headers = [
        "Atividade",
        "Duração",
        "Predecessores (atividade1,atividade2,...)\n caso nao tenha, deixe em branco",
    ]
    for h in headers:
        th = js.document.createElement("th")
        th.innerText = h
        header.appendChild(th)
    table.appendChild(header)

    for i in range(num_activities):
        row = js.document.createElement("tr")

        activity_input = js.document.createElement("input")
        activity_input.setAttribute("type", "text")
        activity_input.setAttribute("id", f"activity_{i}")

        duration_input = js.document.createElement("input")
        duration_input.setAttribute("type", "number")
        duration_input.setAttribute("id", f"duration_{i}")

        predecessors_input = js.document.createElement("input")
        predecessors_input.setAttribute("type", "text")
        predecessors_input.setAttribute("id", f"predecessors_{i}")

        activity_td = js.document.createElement("td")
        duration_td = js.document.createElement("td")
        predecessors_td = js.document.createElement("td")

        activity_td.appendChild(activity_input)
        duration_td.appendChild(duration_input)
        predecessors_td.appendChild(predecessors_input)

        row.appendChild(activity_td)
        row.appendChild(duration_td)
        row.appendChild(predecessors_td)

        table.appendChild(row)

    activities_input_div.appendChild(table)

    submit_activities_button = js.document.createElement("button")
    submit_activities_button.innerText = "Submit Activities Data"
    submit_activities_button.addEventListener("click", create_proxy(create_graph))
    activities_input_div.appendChild(submit_activities_button)


def create_graph(event):
    import matplotlib.pyplot as plt
    import networkx as nx
    from io import BytesIO
    import base64
    from PIL import Image

    num_activities = int(js.document.getElementById("num_activities").value)
    activities = {}

    for i in range(num_activities):
        activity = js.document.getElementById(f"activity_{i}").value
        duration = int(js.document.getElementById(f"duration_{i}").value)
        predecessors = js.document.getElementById(f"predecessors_{i}").value
        predecessors = (
            [pred.strip() for pred in predecessors.split(",")] if predecessors else []
        )
        activities[activity] = {"duration": duration, "predecessors": predecessors}

    early_start, early_finish, late_start, late_finish = calculate_pert_cpm(activities)
    display_pert_cpm(activities, early_start, early_finish, late_start, late_finish)
    plot_pert_cpm(activities, early_start, late_start)


def calculate_pert_cpm(activities):
    early_start = {}
    early_finish = {}
    late_start = {}
    late_finish = {}

    sorted_activities = []
    while len(sorted_activities) < len(activities):
        for activity in activities:
            if activity not in sorted_activities and all(
                pred in sorted_activities
                for pred in activities[activity]["predecessors"]
            ):
                sorted_activities.append(activity)

    for activity in sorted_activities:
        es = max(
            [early_finish[pred] for pred in activities[activity]["predecessors"]],
            default=0,
        )
        early_start[activity] = es
        early_finish[activity] = es + activities[activity]["duration"]

    for activity in reversed(sorted_activities):
        lf = min(
            [
                late_start[succ]
                for succ in activities
                if activity in activities[succ]["predecessors"]
            ],
            default=max(early_finish.values()),
        )
        late_finish[activity] = lf
        late_start[activity] = lf - activities[activity]["duration"]

    return early_start, early_finish, late_start, late_finish


def display_pert_cpm(activities, early_start, early_finish, late_start, late_finish):
    output_div = js.document.getElementById("output")
    output_div.innerHTML = ""

    table = js.document.createElement("table")
    table.setAttribute("style", "border-collapse: collapse; width: 100%;")

    header = js.document.createElement("tr")

    headers = ["Activity", "Early Start", "Early Finish", "Late Start", "Late Finish"]
    for h in headers:
        th = js.document.createElement("th")
        th.innerText = h
        th.setAttribute(
            "style", "border: 1px solid black; padding: 8px; text-align: center;"
        )
        header.appendChild(th)
    table.appendChild(header)

    for activity in activities:
        row = js.document.createElement("tr")
        cells = [
            activity,
            early_start[activity],
            early_finish[activity],
            late_start[activity],
            late_finish[activity],
        ]
        for cell in cells:
            td = js.document.createElement("td")
            td.innerText = cell
            td.setAttribute(
                "style", "border: 1px solid black; padding: 8px; text-align: center;"
            )
            row.appendChild(td)
        table.appendChild(row)

    output_div.appendChild(table)

    critical_path = [
        activity
        for activity in activities
        if early_start[activity] == late_start[activity]
    ]
    critical_path_div = js.document.createElement("div")
    critical_path_div.innerText = f"\nCaminho Crítico: {' -> '.join(critical_path)}"
    output_div.appendChild(critical_path_div)


def plot_pert_cpm(activities, early_start, late_start):
    import matplotlib.pyplot as plt
    import networkx as nx
    from io import BytesIO
    import base64

    G = nx.DiGraph()

    for activity, data in activities.items():
        G.add_node(
            activity,
            duration=data["duration"],
            ES=early_start[activity],
            LS=late_start[activity],
        )
        for pred in data["predecessors"]:
            G.add_edge(pred, activity)

    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 8))
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color="lightblue",
        node_size=3000,
        font_size=10,
        font_weight="bold",
    )

    labels = {node: f"{node}" for node in G.nodes}
    es_ls_labels = {
        node: f"ES: {early_start[node]}\nLS: {late_start[node]}" for node in G.nodes
    }

    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold")

    offset = 0.075
    for node, (x, y) in pos.items():
        plt.text(
            x + offset,
            y - offset,
            es_ls_labels[node],
            fontsize=14,
            ha="center",
            va="center",
            bbox=dict(facecolor="white", alpha=0.5, edgecolor="none"),
        )

    # Adjust the subplot to increase the bottom margin
    plt.subplots_adjust(bottom=0.2)

    # Save the figure to a buffer
    buf = BytesIO()
    plt.savefig(buf, format="jpeg")
    buf.seek(0)

    # Convert the buffer to a data URL
    data_url = "data:image/jpeg;base64," + base64.b64encode(buf.read()).decode("utf-8")

    # Display the image
    try:
        from IPython.display import display, HTML

        display(HTML(f'<img src="{data_url}"/>'))
    except ImportError:
        # If IPython is not available, use an alternative method to display the image
        graph_div = js.document.getElementById("graph")
        graph_div.innerHTML = ""
        img_element = js.document.createElement("img")
        img_element.setAttribute("src", data_url)
        graph_div.appendChild(img_element)


js.document.getElementById("submit_activities").addEventListener(
    "click", create_proxy(get_activity_data)
)
