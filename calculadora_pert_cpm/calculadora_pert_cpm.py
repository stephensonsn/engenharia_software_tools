import networkx as nx
import matplotlib.pyplot as plt

def get_activity_data():
    num_activities = int(input("Digite o número de atividades: "))
    activities = {}
    
    for i in range(num_activities):
        activity = input(f"Digite a atividade {i+1}: ")
        duration = int(input(f"Digite a duração da atividade {activity}: "))
        predecessors = input(f"Digite os predecessores da atividade {activity} (separados por vírgula, deixe em branco se não houver): ")
        predecessors = predecessors.split(',') if predecessors else []
        activities[activity] = {"duration": duration, "predecessors": predecessors}
    
    return activities

def create_graph(activities):
    G = nx.DiGraph()
    
    for activity, data in activities.items():
        G.add_node(activity, duration=data["duration"])
        for pred in data["predecessors"]:
            G.add_edge(pred.strip(), activity)
    
    return G

def calculate_pert_cpm(G):
    early_start = {}
    early_finish = {}
    late_start = {}
    late_finish = {}
    
    for node in nx.topological_sort(G):
        es = max([early_finish[pred] for pred in G.predecessors(node)], default=0)
        early_start[node] = es
        early_finish[node] = es + G.nodes[node]['duration']
    
    for node in reversed(list(nx.topological_sort(G))):
        lf = min([late_start[succ] for succ in G.successors(node)], default=max(early_finish.values()))
        late_finish[node] = lf
        late_start[node] = lf - G.nodes[node]['duration']
    
    return early_start, early_finish, late_start, late_finish

def display_pert_cpm(activities, early_start, early_finish, late_start, late_finish):
    print("\nActivity\tES\tEF\tLS\tLF")
    for activity in activities:
        print(f"{activity}\t\t{early_start[activity]}\t{early_finish[activity]}\t{late_start[activity]}\t{late_finish[activity]}")
    
    critical_path = [activity for activity in activities if early_start[activity] == late_start[activity]]
    print(f"\nCaminho Crítico: {' -> '.join(critical_path)}")

def plot_pert_cpm(G, early_start, late_start):
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, font_weight='bold')
    
    labels = {node: f"{node}\nES: {early_start[node]}\nLS: {late_start[node]}" for node in G.nodes}
    nx.draw_networkx_labels(G, pos, labels, font_size=8)
    
    plt.show()

if __name__ == "__main__":
    activities = get_activity_data()
    G = create_graph(activities)
    early_start, early_finish, late_start, late_finish = calculate_pert_cpm(G)
    display_pert_cpm(activities, early_start, early_finish, late_start, late_finish)
    plot_pert_cpm(G, early_start, late_start)
