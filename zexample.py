import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch
from matplotlib.collections import PatchCollection
from planning import *
import re
import random
import numpy as np
from difflib import get_close_matches
from parser_AS_why_a import *
from parser1_AS_why_A_not_B import*
from parser2_AS_why_A_not_B import *
from decimal import Decimal, getcontext

class Support:
    def __init__(self, name):
        self.name = name
        self.postconditions = set()  # Initialize postconditions as a set

    def add_postcondition(self, *postconditions):
        self.postconditions.update(postconditions)  # Add multiple items to the postconditions set

    def remove_postcondition(self, *postconditions):
        for postcondition in postconditions:
            self.postconditions.discard(postcondition)  # Remove items from the postconditions set if they exist

    def show_postconditions(self):
        return self.postconditions  # Return the set of postconditions
    
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return f"Support({self.name})"


class Argument(Support):  # Inheriting from Support to make Support instances also Arguments
    def __init__(self, name, chosen):
        super().__init__(name)
        self.attacks = set()
        self.supports = set()  # Initialize supports as a set of Support instances
        self.chosen = chosen
        self.objects = set()

    def add_attack(self, *attacks):
        self.attacks.update(attacks)  # Add multiple items to the attacks set

    def remove_attack(self, *attacks):
        for attack in attacks:
            self.attacks.discard(attack)  # Remove items from the attacks set if they exist

    def add_support(self, *supports):
        self.supports.update(supports)  # Add multiple Support instances to the supports set

    def remove_support(self, *supports):
        for support in supports:
            self.supports.discard(support)  # Remove Support instances from the supports set if they exist

    def add_objects(self, *objects):
        self.objects.update(objects)  # Add multiple attributes to the action

    def show_attacks(self):
        return self.attacks  # Return the set of attacks

    def show_supports(self):
        return self.supports  # Return the set of supports

    def show_objects(self):
        return self.objects
    
    def is_supported_by(self, argument):
        # Check if the argument is in the supports set
        return argument in self.supports

    def search_postcondition_in_all_supports(self, postcondition):
        # Check if the postcondition exists in any of the supports
        for support in self.supports:
            if postcondition in support.show_postconditions():
                return support
        return None

def selected_action_and_count(argument,arguments,pos):
    action_name = argument.name
    count = 0
    post_count = 0
    for i,arg in enumerate(arguments):
        if action_name == arg.name:
            count=count+1
            if i > pos:
                post_count = post_count+1
    return action_name,count,post_count

def replacement_action_and_time(argument_name, index, plan1):


    pattern = r'(\d+\.\d+):\s*\((.*?)\)'
    matches = re.findall(pattern, plan1)
    
    # Create a list of tuples (time, description) from the matches
    plan_list = [(float(match[0]), match[1].strip()) for match in matches]

    if index < 0 or index >= len(plan_list):
        raise IndexError("Index out of bounds")

    replacement_action_time, replacement_action_description = plan_list[index]
    

    previous_index = index - 1
    
    if previous_index < 0:
        return argument_name, replacement_action_time, replacement_action_time 
    previous_action_time, previous_action_description = plan_list[previous_index]
    print(f"Action Description at Index {previous_index}: {previous_action_description}")
    print(f"Time at Index {previous_index}: {previous_action_time}")

    return str(previous_action_description), previous_action_time, replacement_action_time

def action_time(prev_action, plan2_1st, durative):
    pattern = r'(\d+\.\d+):\s*\((.*?)\)\s*\[(\d+\.\d+)\]'
    matches = re.findall(pattern, plan2_1st)
    
    plan_list = [(float(match[0]), match[1].strip(), float(match[2])) for match in matches]

    for action_time, action_description, bracket_time in plan_list:
        if prev_action in action_description:
            if durative:
                return action_time + bracket_time
            else:
                return action_time

    return None

def extract_plan_segment(plan_seg, prev_time_num, action_name,index):
    if index == 0:
        return ''
    lines = plan_seg.strip().split('\n')
    result_lines = []
    include_lines = False
    
    for line in lines:
        timestamp_str, action = line.split(': ', 1)
        timestamp = float(timestamp_str)
        if timestamp <= prev_time_num:
            result_lines.append(line)
            if timestamp == prev_time_num and action_name in action:
                include_lines = True
                break
        else:
            break
    if include_lines:
        return '\n'.join(result_lines)
    else:
        return ''
    
def adjust_timestamps(plan_seg, time_offset, durative):
    # Set high precision for Decimal operations
    getcontext().prec = 20

    time_offset = Decimal(time_offset)
    
    # Split the input into lines
    lines = plan_seg.strip().split('\n')
    
    if durative:
        timestamps = []
        actions = []
        durations = []
        
        for line in lines:
            try:
                # Split the line into timestamp and the rest
                timestamp_str, rest = line.split(': ', 1)
                # Further split the rest into action part and duration part
                action_part, duration_part = rest.split(' [', 1)
                duration_str = duration_part.strip(']')
                
                # Append parsed values
                timestamps.append(Decimal(timestamp_str))
                actions.append(action_part.strip())
                durations.append(Decimal(duration_str))
            except ValueError:
                print(f"Skipping malformed line: {line}")
                continue
        
        # Track the last end time and the last timestamp for similar actions
        last_end_time = Decimal('0.00000')
        action_last_time = {}
        
        adjusted_lines = []
        
        for i in range(len(timestamps)):
            timestamp = timestamps[i]
            duration = durations[i]
            action = actions[i]
            
            # Calculate the end time of the current action
            end_time = timestamp + duration
            
            # Adjust the timestamp if it's less than or equal to the last end time
            if timestamp <= last_end_time:
                timestamp = last_end_time + Decimal('0.001')
            
            # Adjust timestamp for common actions
            if action in action_last_time:
                action_last_time[action] += Decimal('0.001')
                timestamp = max(timestamp, action_last_time[action])
            else:
                action_last_time[action] = timestamp
            
            # Update the end time of the current action
            last_end_time = timestamp + duration
            
            # Determine max decimal length for formatting
            max_decimal_length = max(len(str(timestamp).split('.')[1]), len(str(duration).split('.')[1]))
            adjusted_line = f"{timestamp:.{max_decimal_length}f}: {action} [{duration:.{max_decimal_length}f}]"
            
            adjusted_lines.append(adjusted_line)
        
        return '\n'.join(adjusted_lines)

    else:
        timestamps = []
        actions = []
        
        for line in lines:
            try:
                # Split the line into timestamp and action
                timestamp_str, action = line.split(': ', 1)
                
                # Append parsed values
                timestamps.append(Decimal(timestamp_str))
                actions.append(action)
            except ValueError:
                print(f"Skipping malformed line: {line}")
                continue
        
        # Determine max decimal length for formatting
        max_decimal_length = max((len(str(ts).split('.')[1]) if '.' in str(ts) else 0) for ts in timestamps)
        
        adjusted_lines = []
        
        for timestamp, action in zip(timestamps, actions):
            adjusted_timestamp = timestamp + time_offset
            if '.' in str(timestamp):
                adjusted_line = f"{adjusted_timestamp:.{max_decimal_length}f}: {action}"
            else:
                adjusted_line = f"{adjusted_timestamp:.0f}: {action}"
            
            adjusted_lines.append(adjusted_line)
        
        return '\n'.join(adjusted_lines)


def combine_plan(*plan_segs):
    combined_plan = []
    for plan_segs in plan_segs:
        combined_plan.append(plan_segs)
    return '\n'.join(combined_plan)

def check_postconditions_supporting_arguments(argument, arguments):
    argument.chosen = 1
    if argument == selected_arg:
        arg_oc.add_support(argument)
    results = []
    postconditions = argument.show_postconditions()  # Get the postconditions of the argument to check
    for other_argument in arguments:
        if other_argument != argument:  # Skip the argument itself
            for support in other_argument.show_supports():
                if support in postconditions:
                    results.append((other_argument.name, support))
    return results


def set_chosen(results, arguments):
    goal_present = False

    # Check if "Goal" is present in results
    for arg_name, postcondition in results:
        if arg_name == "Goal":
            goal_present = True
            break

    if goal_present:
        # Set the chosen attribute for the "Goal" argument
        goal_argument = next((arg for arg in arguments if arg.name == "Goal"), None)
        if goal_argument:
            goal_argument.chosen = 1
            # Set the chosen attribute for the associated arguments
            associated_argument = next((arg for arg in arguments if arg.name == postcondition.name), None)
            if associated_argument:
                associated_argument.chosen = 1
    else:
        # Find the first common action present in the list of arguments
        common_action = None
        for arg_name, postcondition in results:
            if arg_name != "Goal":
                common_action = next((arg for arg in arguments if arg.name == arg_name), None)
                if common_action:
                    break

        if common_action:
            common_action.chosen = 1
            # Set the chosen attribute for the associated arguments
            associated_argument = next((arg for arg in arguments if arg.name == postcondition.name), None)
            if associated_argument:
                associated_argument.chosen = 1

def set_objects_chosen(argument):
    for obj in argument.objects:
        obj.chosen = 1
       
def prune_list(lst, index):

    # Adjust index for Python's negative index support
    if index < -len(lst):
        index = -len(lst) - 1  # Adjust to ensure no elements are returned
    
    # Return the slice of the list after the given index
    return lst[index:]

def create_argument_list(actionlist, arguments):
    argument_names = [arg.name.lower() for arg in arguments]
    present_arguments = []

    for action in actionlist:
        action_name = action.lower()
        
        # Find the closest matches for the action name
        closest_matches = get_close_matches(action_name, argument_names, n=1, cutoff=0.0)
        
        if closest_matches:
            closest_match = closest_matches[0]
            present_arguments.append(arguments[argument_names.index(closest_match)])

    present_arguments.append(arg_goal)
    return present_arguments
# Function to list all chosen arguments
def list_chosen_arguments(arguments):
    chosen_argument_names = []
    chosen_arguments = []
    
    for arg in arguments:
        if arg.chosen == 1:
            chosen_argument_names.append(arg.name)
            chosen_arguments.append(arg)
    
    return chosen_argument_names, chosen_arguments


def create_argument_graph(args):
    graph = nx.DiGraph()

    # Add only chosen arguments as nodes
    for argument in args:
        graph.add_node(argument.name, chosen=argument.chosen)
    
    # Add supports, attacks, and postconditions as directed edges
    for argument in args:
        for support in argument.show_supports():
            if support.chosen == 1:
                graph.add_edge(support.name, argument.name, edge_type='support')
        for attack in argument.show_attacks():
            if attack.chosen == 1:
                graph.add_edge(attack.name, argument.name, edge_type='attack')
        for postcondition in argument.show_postconditions():
            if postcondition.chosen == 1:
                graph.add_edge(argument.name, postcondition.name, edge_type='postcondition')
        for object in argument.show_objects():
            if object.chosen == 1:
                graph.add_edge(object.name, argument.name, edge_type='object')

    return graph

# def visualize_argument_graph(graph):
#     if replacement == True:
#         node_space = 500
#         epochs = 15000
#         sd = 1000
#     else:
#         node_space = 1.1
#         epochs = 150
#         sd =25
#     pos = nx.spring_layout(graph, iterations=epochs, seed=sd, k=node_space)  # Increase k for more space between nodes
#     edge_types = nx.get_edge_attributes(graph, 'edge_type')
    
#     # Remove 'chosen' from node labels
#     node_labels = {node: f"{node}" for node in graph.nodes()}
    
#     plt.figure(figsize=(12, 8))
    
#     # Calculate node sizes based on label length
#     node_sizes = [len(label) * 5 for label in node_labels.values()]
    
#     # Draw nodes
#     nx.draw_networkx_nodes(graph, pos, node_color='white', edgecolors='white', node_size=node_sizes)
#     nx.draw_networkx_labels(graph, pos, font_size=9, labels=node_labels)
    
#     # Draw edges with different styles and colors on top of nodes
#     for edge_type in set(edge_types.values()):
#         if edge_type == 'support':
#             edge_color = 'green'
#             style = 'solid'
#             arrow_direction = 1
#             label = "Support"
#         elif edge_type == 'attack':
#             edge_color = 'red'
#             style = 'solid'
#             arrow_direction = 1
#             label = "Attack"
#         elif edge_type == 'postcondition':
#             edge_color = 'green'  
#             style = 'solid'
#             arrow_direction = 1 
#             label = "Support"
#         elif edge_type == 'object':
#             edge_color = 'black'
#             style = 'solid'
#             arrow_direction = 1
#             label = "Object"  
#         edges = [(u, v) if arrow_direction == 1 else (v, u) for u, v, d in graph.edges(data=True) if d['edge_type'] == edge_type]
        
#         # Customize arrow style and connection to node border
#         arrow_style = "-|>"
#         connection_style = "arc3,rad=0.2"  # Add curvature to edges to reduce overlap
        
#         nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color=edge_color, style=style, arrows=True, arrowsize=20,
#                                 arrowstyle=arrow_style, connectionstyle=connection_style, width=2) #
        
#         nx.draw_networkx_edge_labels(graph, pos, edge_labels={(u, v) if arrow_direction == 1 else (v, u): label for u, v in edges}, font_color='black', font_size=8)
    
#     if cost2 == float('inf'):
#         plt.text(0.5, 1.05, f"Plan cannot be solved: {selected_action} was a critical action", horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes, fontsize=12, color='red', weight='bold')
    
#     plt.axis('on')
#     plt.show(block=False)

    


def display_plans(p1, p2):

    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    axes[0].text(0.5, 0.5, p1, fontsize=12, ha='center', va='center', wrap=True)
    axes[0].set_title('Original Plan')
    axes[0].axis('off')  

    axes[1].text(0.5, 0.5, p2, fontsize=12, ha='center', va='center', wrap=True)
    axes[1].set_title('New Plan')
    axes[1].axis('off')  

    plt.tight_layout()

    plt.show()  
    
def visualize_argument_graph(graph):
    # Define layout parameters based on replacement
    if replacement:
        node_space = 3.4
        epochs = 150
        sd = 25
    else:
        node_space = 1.1
        epochs = 150
        sd = 25

    # Define node positions using spring layout
    pos = nx.spring_layout(graph, iterations=epochs, seed=sd, k=node_space)
    node1 = 'prepare_dish chicken order2 chef1'
    pos[node1] = (pos[node1][0]*1.8, pos[node1][1]* 1.8)
    node2 = 'prepared order2 chicken'
    pos[node2] = (pos[node2][0]*40, pos[node2][1]* -1.8)
    node3 = 'cook_dish chicken order2 ovenshelf1'
    pos[node3] = (pos[node3][0]*-1.8, pos[node3][1] )
    node4 = 'original cost(67.003)'
    pos[node4] = (pos[node4][0]*-10, pos[node4][1]*10 )
    node5 = 'new cost(72.003)'
    pos[node5] = (pos[node5][0], pos[node5][1]*1.8 )
    node6 = 'new plan'
    pos[node6] = (pos[node6][0]*-1.5, pos[node6][1]*-4 )
    node7 = 'original plan'
    pos[node7] = (pos[node7][0], pos[node7][1]*2.5 )
    node8 = 'preparation_time(chicken) = 2'
    pos[node8] = (pos[node8][0]*3, pos[node8][1]*-2 )
    node9 = 'order1'
    pos[node9] = (pos[node9][0]*-3, pos[node9][1]*-2 )
    node10 = 'cooking_time(lasagne) = 35'
    pos[node10] = (pos[node10][0]-3, pos[node10][1]*2 )
    node11 = 'prepared order1 lasagne'
    pos[node11] = (pos[node11][0]*2, pos[node11][1]* 15)
    # for node in pos:
    #     coin1 = random.randint(0,5)
    #     coin2 = random.randint(0,5)
    #     pos[node] = (pos[node][0] +coin1, pos[node][1]+coin2)
    # for node in pos:
    #     coin = random.randint(0,1)
    #     print(coin)
    #     if coin == 0:
    #         pos[node] = (pos[node][0] * 5, pos[node][1]*10)
    #     else:
    #         pos[node] = (pos[node][0]* 10 , pos[node][1]* 5)
    # Edge types and node labels
    edge_types = nx.get_edge_attributes(graph, 'edge_type')
    node_labels = {node: f"{node}" for node in graph.nodes()}

    # Create figure
    plt.figure(figsize=(60, 40))  # Larger figure for better spacing
    
    # Calculate node sizes based on label length
    node_sizes = [len(label) * 1 for label in node_labels.values()]

    # Draw nodes
    nx.draw_networkx_nodes(graph, pos, node_color='white', edgecolors='white', node_size=node_sizes)
    nx.draw_networkx_labels(graph, pos, font_size=10, labels=node_labels,verticalalignment='center', horizontalalignment='center')

    # Draw edges with different styles and colors
    for edge_type in set(edge_types.values()):
        if edge_type == 'support':
            edge_color = 'green'
            label = "Support"
        elif edge_type == 'attack':
            edge_color = 'red'
            label = "Attack"
        elif edge_type == 'postcondition':
            edge_color = 'green'
            label = "Support"
        elif edge_type == 'object':
            edge_color = 'black'
            label = "Object"
        
        # Prepare edges for drawing
        edges = [(u, v) for u, v, d in graph.edges(data=True) if d['edge_type'] == edge_type]
        
        # Customize arrow style and connection to node border
        arrow_style = "-|>"
        connection_style = "arc3,rad=0.2"  # Add curvature to edges
        nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color=edge_color, style='solid', arrows=True, arrowsize=20,
                                arrowstyle=arrow_style, connectionstyle=connection_style, width=2)
        
        # Draw edge labels
        #nx.draw_networkx_edge_labels(graph, pos, edge_labels={(u, v): label for u, v in edges}, font_color='black', font_size=9)
    
    # Display critical action text if applicable
    if cost2 == float('inf'):
        plt.text(0.5, 1.05, f"Plan cannot be solved: {selected_action} was a critical action", horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes, fontsize=12, color='red', weight='bold')
    elif cost2 == -1:
        plt.text(0.5, 1.05, f"Internal error in the planner", horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes, fontsize=12, color='red', weight='bold')
    plt.axis('on')
    plt.show(block=False)



    
replacement = True
cost1= 67.00300
cost2= 72.00300
domain_file = 'D:/aip/dur/cafedomain.pddl'
problem_file = 'D:/aip/dur/cafeproblem.pddl'
new_domain_file = 'D:/aip/newdur/newcafedomain.pddl'
new_problem_file = 'D:/aip/newdur/newcafeproblem.pddl'

main_planfile = 'D:/aip/domain_and_problem/plan.plan'
new_planfile = 'D:/aip/new_domain_and_problem/newplan.plan'
durative = True
#objects
# Define individual arguments
arg_chicken = Argument("chicken", 0)
arg_lasagne = Argument("lasagne", 0)
arg_oven = Argument("ovenshelf1", 0)
arg_chef = Argument("chef1", 0)
arg_o1 = Argument("order1",0)
arg_o2 = Argument("order2",0)
arg_freeo = Argument("free ovenshelf1", 0)
arg_freech = Argument("chef_free chef1", 0)
arg_ol = Argument("ordered order1 lasagne",0)
arg_oc = Argument("ordered order2 chicken",0)
arg_nol = Argument("not order_placed order1 lasagne",0)
arg_noc = Argument("not order_placed order2 chicken",0)

# Preparation and cooking times
arg_preptimel = Argument("preparation_time(lasagne) = 5", 0)
arg_cooktimel = Argument("cooking_time(lasagne) = 35", 1)
arg_preptimec = Argument("preparation_time(chicken) = 2", 0)
arg_cooktimec = Argument("cooking_time(chicken) = 30", 1)

# Preparation and order status
arg_cprepped = Argument("prepared order2 chicken", 0)
arg_lprepped = Argument("prepared order1 lasagne", 0)
arg_ncprepped = Argument("not prepared order2 chicken", 0)
arg_nlprepped = Argument("not prepared order1 lasagne", 0)

arg_opc = Argument("order_placed order1 chicken", 0)
arg_opl = Argument("order_placed order2 lasagne", 0)
arg_rc = Argument("ready order1 chicken", 0)
arg_rl = Argument("ready order2 lasagne", 0)
arg_nrc = Argument("not ready order1 chicken", 0)
arg_nrl = Argument("not ready order2 lasagne", 0)

# Create arguments for plans and costs
arg_op = Argument("original plan", 1)
arg_np = Argument("new plan", 1)
arg_oc = Argument(f"original cost {cost1}", 1)
arg_nc = Argument(f"new cost {cost2}", 1)
arg_goal = Argument("Goal", 0)

# Actions related to cooking and delivery
arg_prepc = Argument("prepare_dish chicken order2 chef1", 0)
arg_prepl = Argument("prepare_dish lasagne order1 chef1", 0)
arg_cookc = Argument("cook_dish chicken order2 ovenshelf1", 0)
arg_cookl = Argument("cook_dish lasagne order1 ovenshelf1", 0)
arg_dc = Argument("deliver_dish order2 chicken", 0)
arg_dl = Argument("deliver_dish order1 lasagne", 0)
arg_doc = Argument("delivered order2 chicken", 0)
arg_dol = Argument("delivered order1 lasagne", 0)
# List of all arguments
arguments = [
    arg_chicken, arg_lasagne, arg_oven, arg_chef, arg_freeo, arg_freech,
    arg_preptimel, arg_cooktimel, arg_preptimec, arg_cooktimec,
    arg_cprepped, arg_lprepped, arg_oc, arg_ol, arg_rc, arg_rl,arg_opc, arg_opl,
    arg_op, arg_np, arg_oc, arg_nc, arg_goal,arg_noc, arg_nol,arg_ncprepped,arg_nlprepped,arg_nrc,arg_nrl,
    arg_prepc, arg_prepl, arg_cookc, arg_cookl, arg_dc, arg_dl,arg_doc, arg_dol, arg_o1,arg_o2
]

plan1 = '0.00000: (prepare_dish chicken order2 chef1)  [2.00000]\n 2.00100: (cook_dish chicken order2 ovenshelf1)  [30.00000]\n 2.00100: (prepare_dish lasagne order1 chef1)  [5.00000]\n 32.00200: (cook_dish lasagne order1 ovenshelf1)  [35.00000]\n 32.00200: (deliver_dish order2 chicken)  [2.00000]\n 67.00300: (deliver_dish order1 lasagne)  [2.00000] \n'
plan2 = '0.00000: (prepare_dish lasagne order1 chef1)  [5.00000]\n 5.00100: (cook_dish lasagne order1 ovenshelf1)  [35.00000]\n 5.00100: (prepare_dish chicken order2 chef1)  [2.00000]\n 40.00200: (cook_dish chicken order2 ovenshelf1)  [30.00000]\n 40.00200: (deliver_dish order1 lasagne)  [2.00000]\n 70.00300: (deliver_dish order2 chicken)  [2.00000]\n'
actionlist1,durative_times = action_list(plan1,durative)
print(actionlist1)
# print("Cost:", cost1)

selected_arg = arg_prepc
index = 1
selected_action  = selected_arg.name
replacement_arg = arg_prepl

# Call the function to create a list of present arguments
present_arguments1 = create_argument_list(actionlist1, arguments)
print("present arguments")
print([arg.name for arg in present_arguments1])

actionlist2,durative_times = action_list(plan2,durative)
if plan2 != "not solvable":
    if cost1 > cost2:
        arg_op.add_attack(arg_np)

    elif cost1 < cost2:
        arg_np.add_attack(arg_op)
    
    else:
        arg_op.add_attack(arg_np)
        arg_np.add_attack(arg_op)
else:
    print("Plan is not solvable.")
    arg_op.add_attack(arg_np)



arg_op.add_support(arg_oc)
arg_np.add_support(arg_nc)

arg_nc.name = f"new cost({cost2})"
arg_oc.name = f"original cost({cost1})"

if replacement==True:
    arg_nc.add_support(replacement_arg)
    present_arguments2 = create_argument_list(actionlist2, arguments)


# Add supports to their respective arguments based on the domain (needs to be changed for every domain)

arg_prepc.add_postcondition(arg_cprepped,arg_freech,arg_noc)
arg_prepc.add_support(arg_freech,arg_oc,arg_opc)
arg_cookc.add_postcondition(arg_freeo,arg_ncprepped,arg_rc)
arg_cookc.add_support(arg_cprepped,arg_freeo,arg_oc)
arg_dc.add_postcondition(arg_nrc,arg_doc)
arg_dc.add_support(arg_rc,arg_oc)

arg_prepl.add_postcondition(arg_lprepped,arg_freech,arg_nol)
arg_prepl.add_support(arg_freech,arg_ol,arg_opl)
arg_cookl.add_postcondition(arg_freeo,arg_nlprepped,arg_rl)
arg_cookl.add_support(arg_lprepped,arg_freeo,arg_ol)
arg_dc.add_postcondition(arg_nrl,arg_dol)
arg_dc.add_support(arg_rl,arg_ol)

arg_goal.add_support(arg_dc,arg_dl)

arg_prepc.add_objects(arg_chicken,arg_o2,arg_preptimec)
arg_cookc.add_objects(arg_chicken,arg_o2,arg_cooktimec)
arg_dc.add_objects(arg_chicken)
arg_prepl.add_objects(arg_lasagne,arg_o1,arg_preptimel)
arg_cookl.add_objects(arg_chicken,arg_o2,arg_cooktimel)
arg_dl.add_objects(arg_lasagne)






pruned_list1 = prune_list(present_arguments1,index)
print(pruned_list1)
results1 = check_postconditions_supporting_arguments(selected_arg, pruned_list1)
print(f"results1 {results1}")
for result in results1:
    print(f"Postcondition {result[1].name} of argument {selected_arg.name} supports argument {result[0]}")

set_chosen(results1, arguments)
if selected_arg.show_objects:
    set_objects_chosen(selected_arg)

if replacement == True:
    pruned_list2 = prune_list(present_arguments2,index)
    print(pruned_list2)
    results2 = check_postconditions_supporting_arguments(replacement_arg, present_arguments2)
    print(f"results2 {results2}")
    for result in results2:
        print(f"Postcondition {result[1].name} of argument {replacement_arg.name} supports argument {result[0]}")
    set_chosen(results2, arguments)
    if replacement_arg.show_objects:
        set_objects_chosen(replacement_arg)


chosen_argument_names,chosen_arguments = list_chosen_arguments(arguments)
print("Chosen arguments:", chosen_argument_names)


graph = create_argument_graph(chosen_arguments)
visualize_argument_graph(graph)

display_plans(plan1,plan2)
