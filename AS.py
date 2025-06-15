import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch
from matplotlib.collections import PatchCollection
from planning import *
from menu import *
import re
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

# extract selected actiona and the number of times it is repeated
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

# extract the replacement action and the time at which it occurs
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
        return argument_name, -1, replacement_action_time 
    previous_action_time, previous_action_description = plan_list[previous_index]
    print(f"Action Description at Index {previous_index}: {previous_action_description}")
    print(f"Time at Index {previous_index}: {previous_action_time}")

    return str(previous_action_description), previous_action_time, replacement_action_time

# extract the previous action time wrt selected action
def action_time(prev_action, plan2_1st, durative):
    if durative == True:
        pattern = r'(\d+\.\d+):\s*\((.*?)\)\s*\[(\d+\.\d+)\]'
        matches = re.findall(pattern, plan2_1st)
        
        plan_list = [(float(match[0]), match[1].strip(), float(match[2])) for match in matches]

        for action_time, action_description, bracket_time in plan_list:
            if prev_action in action_description:
                    return action_time + bracket_time
    else:
        pattern = r'(\d+\.\d+):\s*\((.*?)\)'
        matches = re.findall(pattern, plan2_1st)
        
        plan_list = [(float(match[0]), match[1].strip()) for match in matches]

        for action_time, action_description in plan_list:
            if prev_action in action_description:
                    return action_time

    return None

# Extract sequence of actions executed before the questioned actions
def extract_plan_segment(plan_seg, prev_time_num, action_name,index):
    if index == 0:
        return ''
    lines = plan_seg.strip().split('\n')
    result_lines = []
    include_lines = False
    
    # Parse through the lines to extract the plan before the questioned action
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

# Correction of time stamps post transformations
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
            
            # To maintain formatting determine the max decimal length
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

# Combine the plans post transformations
def combine_plan(*plan_segs):
    combined_plan = []
    for plan_segs in plan_segs:
        combined_plan.append(plan_segs)
    return '\n'.join(combined_plan)

# To check the postconditions of the supporting arguments
def check_postconditions_supporting_arguments(argument, arguments):
    argument.chosen = 1
    if argument == selected_arg:
        arg_oc.add_support(argument)
    elif replacement == True and argument == replacement_arg:
        arg_nc.add_support(argument)
    results = []
    postconditions = argument.show_postconditions()  
    for other_argument in arguments:
        if other_argument != argument:  
            for support in other_argument.show_supports():
                if support in postconditions:
                    results.append((other_argument.name, support))
    return results


# select the arguments required to build the line of reasoning
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

# Set the objects of the selected argument and replacement arguments as chosen
def set_objects_chosen(argument):
    for obj in argument.objects:
        obj.chosen = 1

# Prune list of actions to remove actions before the questioned action  
def prune_list(lst, index):

    if index < -len(lst):
        index = -len(lst) - 1  
    return lst[index:]

# create a list of the arguments present in the plan
def create_argument_list(actionlist, arguments):
    argument_names = [arg.name.lower() for arg in arguments]
    present_arguments = []

    for action in actionlist:
        action_name = action.lower()
        
        # Find the closest matches for the action name. 
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
    
    # Iterate through the arguments and add the chosen arguments to the list
    for arg in arguments:
        if arg.chosen == 1:
            chosen_argument_names.append(arg.name)
            chosen_arguments.append(arg)
    
    return chosen_argument_names, chosen_arguments

# create the graph
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
    
# visualize the graph built
def visualize_argument_graph(graph):
    # Define layout parameters based on replacement
    if replacement:
        node_space = 50
        epochs = 1500
        sd = 15
    else:
        node_space = 1.1
        epochs = 150
        sd = 25

    # Define node positions using spring layout
    pos = nx.spring_layout(graph, iterations=epochs, seed=sd, k=node_space)


    # Edge types and node labels
    edge_types = nx.get_edge_attributes(graph, 'edge_type')
    node_labels = {node: f"{node}" for node in graph.nodes()}

    # Create figure
    plt.figure(figsize=(40, 40))  # Larger figure for better spacing
    
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
        
        arrow_style = "-|>"
        connection_style = "arc3,rad=0.2"
        
        nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color=edge_color, style='solid', arrows=True, arrowsize=20,
                                arrowstyle=arrow_style, connectionstyle=connection_style, width=2)
        
        # Draw edge labels
        nx.draw_networkx_edge_labels(graph, pos, edge_labels={(u, v): label for u, v in edges}, font_color='black', font_size=9)
    
    # Error message in case of internal error in the planner or if the plan is unsolvable
    if cost2 == float('inf'):
        plt.text(0.5, 1.05, f"Plan cannot be solved: {selected_action} was a critical action", horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes, fontsize=12, color='red', weight='bold')
    elif cost2 == -1:
        plt.text(0.5, 1.05, f"Internal error in the planner", horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes, fontsize=12, color='red', weight='bold')
    plt.axis('on')
    plt.show(block=False)

cost1= 0
cost2= 0
domain_file = 'D:/aip/domain_and_problem/blocksworld_domain.pddl'
problem_file = 'D:/aip/domain_and_problem/blocksworld_problem.pddl'
new_domain_file = 'D:/aip/new_domain_and_problem/newdomain.pddl'
new_problem_file = 'D:/aip/new_domain_and_problem/newproblem.pddl'
planner_loc = 'D:/aip/'
durative = False


#objects
arg_a = Argument("a", 0)
arg_b = Argument("b", 0)
arg_c = Argument("c", 0)
arg_d = Argument("d", 0)
arg_hc = Argument("hand clean", 0)
arg_hnc = Argument("hand not clean", 0)
arg_hr = Argument("hand yellow", 0)
arg_hy = Argument("hand red", 0)
arg_yellow = Argument("yellow", 0)
arg_red = Argument("red",0)

# core arguments
arg_op = Argument("original plan", 1)
arg_np = Argument("new plan", 1)
arg_oc = Argument(f"original cost({cost1})", 1)
arg_nc = Argument(f"new cost ({cost2})", 1)
arg_goal = Argument("Goal",0)

# action arguments
# Action Pickup
arg_picka = Argument("pick-up a yellow", 0)
arg_pickb = Argument("pick-up b red", 0)
arg_pickc = Argument("pick-up c red", 0)
arg_pickd = Argument("pick-up d yellow", 0)

# Action Pickup Same Colour
arg_picksca = Argument("pick-up-same-colour a yellow", 0)
arg_pickscb = Argument("pick-up-same-colour b red", 0)
arg_pickscc = Argument("pick-up-same-colour c red", 0)
arg_pickscd = Argument("pick-up-same-colour d yellow", 0)

# Action Stack
arg_sab = Argument("stack a b", 0)
arg_sac = Argument("stack a c", 0)
arg_sad = Argument("stack a d", 0)

arg_sba = Argument("stack b a", 0)
arg_sbc = Argument("stack b c", 0)
arg_sbd = Argument("stack b d", 0)

arg_sca = Argument("stack c a", 0)
arg_scb = Argument("stack c b", 0)
arg_scd = Argument("stack c d", 0)

arg_sda = Argument("stack d a", 0)
arg_sdb = Argument("stack d b", 0)
arg_sdc = Argument("stack d c", 0)

# Action Unstack
arg_unab = Argument("unstack a b yellow", 0)
arg_unac = Argument("unstack a c yellow", 0)
arg_unad = Argument("unstack a d yellow", 0)

arg_unba = Argument("unstack b a red", 0)
arg_unbc = Argument("unstack b c red", 0)
arg_unbd = Argument("unstack b d red", 0)

arg_unca = Argument("unstack c a red", 0)
arg_uncb = Argument("unstack c b red", 0)
arg_uncd = Argument("unstack c d red", 0)

arg_unda = Argument("unstack d a yellow", 0)
arg_undb = Argument("unstack d b yellow", 0)
arg_undc = Argument("unstack d c yellow", 0)

# Action Unstack Same Colour
arg_unscab = Argument("unstack-same-colour a b yellow", 0)
arg_unscac = Argument("unstack-same-colour a c yellow", 0)
arg_unscad = Argument("unstack-same-colour a d yellow", 0)

arg_unscba = Argument("unstack-same-colour b a red", 0)
arg_unscbc = Argument("unstack-same-colour b c red", 0)
arg_unscbd = Argument("unstack-same-colour b d red", 0)

arg_unscca = Argument("unstack-same-colour c a red", 0)
arg_unsccb = Argument("unstack-same-colour c b red", 0)
arg_unsccd = Argument("unstack-same-colour c d red", 0)

arg_unscda = Argument("unstack-same-colour d a yellow", 0)
arg_unscdb = Argument("unstack-same-colour d b yellow", 0)
arg_unscdc = Argument("unstack-same-colour d c yellow", 0)

# Action Putdown
arg_puta = Argument("put-down a", 0)
arg_putb = Argument("put-down b", 0)
arg_putc = Argument("put-down c", 0)
arg_putd = Argument("put-down d", 0)


# action clean hand
arg_cleanred = Argument("clean red", 0)
arg_cleanyellow = Argument("clean yellow", 0)

# post conditions
argpost_aonb = Argument("a on b", 0)
argpost_aonc = Argument("a on c", 0)
argpost_aond = Argument("a on d", 0)

argpost_bona = Argument("b on b", 0)
argpost_bonc = Argument("b on c", 0)
argpost_bond = Argument("b on d", 0)

argpost_cona = Argument("c on a", 0)
argpost_conb = Argument("c on b", 0)
argpost_cond = Argument("c on d", 0)

argpost_dona = Argument("d on a", 0)
argpost_donb = Argument("d on b", 0)
argpost_donc = Argument("d on c", 0)

argpost_holda = Argument("holding a", 0)
argpost_holdb = Argument("holding b", 0)
argpost_holdc = Argument("holding c", 0)
argpost_holdd = Argument("holding d", 0)

argpost_aontable = Argument("a on table", 0)
argpost_bontable = Argument("b on table", 0)
argpost_contable = Argument("c on table", 0)
argpost_dontable = Argument("d on table", 0)

arg_cleara = Argument("clear a", 0)
arg_clearb = Argument("clear b", 0)
arg_clearc = Argument("clear c", 0)
arg_cleard = Argument("clear d", 0)




arguments = [
    arg_op, arg_np, arg_oc, arg_nc,
    arg_picka, arg_pickb, arg_pickc, arg_pickd,
    arg_picksca, arg_pickscb, arg_pickscc, arg_pickscd,
    arg_sab, arg_sac, arg_sad,
    arg_sba, arg_sbc, arg_sbd,
    arg_sca, arg_scb, arg_scd,
    arg_sda, arg_sdb, arg_sdc,
    arg_unab, arg_unac, arg_unad,
    arg_unba, arg_unbc, arg_unbd,
    arg_unca, arg_uncb, arg_uncd,
    arg_unda, arg_undb, arg_undc,
    arg_unscab, arg_unscac, arg_unscad,
    arg_unscba, arg_unscbc, arg_unscbd,
    arg_unscca, arg_unsccb, arg_unsccd,
    arg_unscda, arg_unscdb, arg_unscdc,
    arg_puta, arg_putb, arg_putc, arg_putd,
    argpost_aonb, argpost_aonc, argpost_aond,
    argpost_bona, argpost_bonc, argpost_bond,
    argpost_cona, argpost_conb, argpost_cond,
    argpost_donb, argpost_donc, argpost_dona,
    argpost_holda, argpost_holdb, argpost_holdc, argpost_holdd,
    argpost_aontable, argpost_bontable, argpost_contable, argpost_dontable,
    arg_cleara, arg_clearb, arg_clearc, arg_cleard,
    arg_goal, arg_a, arg_b,arg_c,arg_d,arg_hc,arg_hnc,arg_red,arg_yellow,arg_cleanred,arg_cleanyellow
]

# Generate plan and obtain cost
file_name1 = f'{planner_loc}/POPF {domain_file} {problem_file}'
plan1,cost1 = planner(file_name1,0)

actionlist1,durative_times = action_list(plan1,durative)
#print(actionlist1)
# print("Cost:", cost1)



# Call the function to create a list of present arguments
present_arguments1 = create_argument_list(actionlist1, arguments)
# print("present arguments")
# print([arg.name for arg in present_arguments1])
selected_arg,index,replacement = selection(plan1,present_arguments1)
#index = 10

if replacement ==True:
    replacement_arg = rep_selection(arguments)
    plan1,cost1 = planner(file_name1,1)


selected_action, total_count,action_count = selected_action_and_count(selected_arg,present_arguments1,index)
print(f"selected action is {selected_action}")
print(f"total count is {total_count}")
print(f"action count is {action_count}")
if replacement==True:
    prev_action, prev_time_num, curr_time_num= replacement_action_and_time(selected_action,index,plan1)
    print(f"time of previous action {prev_time_num}")
    print(f"prev action is {prev_action}")
    print(f"replacement action {replacement_arg.name}")



#print(durative_times)


if replacement == True:
    plan2_1st = extract_plan_segment(plan1, prev_time_num, prev_action,index)
    when = None
    if durative == True:
        x=int(input("Apply the replacement at start (1) or at end (2):"))
        if x ==1:
            when = 'start'
        else:
            when = 'end'
            if index ==0:
                prev_time_num = 0
            else: 
                prev_time_num = durative_times[index-1]

    process_pddl_AB1(domain_file, problem_file, prev_action, replacement_arg.name, prev_time_num, new_domain_file, new_problem_file,durative,when,index)
    file_name2 = f'{planner_loc}/POPF {new_domain_file} {new_problem_file}'
    plan2_mid,cost2_mid = planner(file_name2,1)
    if plan2_mid != "not solvable":
        print(f'Plan to execute b\n{plan2_mid}')
        cost2_mid = cost2_mid+ curr_time_num
        print(cost2_mid)
        new_time_num= action_time(replacement_arg.name,plan2_mid,durative)
        if new_time_num == 0.0:
            new_time_num = 0
        #print(f"new time {new_time_num}")
        when = 'end'
        process_pddl_AB2(problem_file, replacement_arg.name, new_time_num, new_problem_file,durative,when ,prev_time_num)
        
        file_name2 = f'{planner_loc}/POPF {new_domain_file} {new_problem_file}'
        plan2_2nd,cost2_2nd = planner(file_name2,1)
        if plan2_2nd != "not solvable":
            plan2_mid = adjust_timestamps(plan2_mid,cost2_mid,durative)
            print(f'Plan executed after b\n{plan2_2nd}')
            cost2 = cost2_2nd+0.00100+cost2_mid
            #print(cost2_2nd)
            plan2_2nd = adjust_timestamps(plan2_2nd,(0.00100+cost2_mid),durative)
            plan2 = combine_plan(plan2_1st,plan2_mid,plan2_2nd)



else:
    if action_count >=1:
        threshold = total_count
        process_pddl_A(domain_file, problem_file, selected_action, threshold, new_domain_file, new_problem_file)
    elif action_count==0:
        threshold = 1
        process_pddl_A(domain_file, problem_file, selected_action, threshold, new_domain_file, new_problem_file)
    
    file_name2 = f'{planner_loc}/POPF {new_domain_file} {new_problem_file}'
    plan2,cost2 = planner(file_name2,0)
    print(plan2)

if plan2 != "not solvable":
    actionlist2,durative_times = action_list(plan2,durative)
    #print("Actions 2:", actionlist2)
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
    present_arguments2 = create_argument_list(actionlist2, arguments)


# Add supports to their respective arguments based on the domain (needs to be changed for every domain)

arg_picka.add_postcondition(argpost_holda)
arg_picka.add_support(arg_cleara,arg_hc)
arg_picksca.add_postcondition(argpost_holda,arg_hy)
arg_picksca.add_support(arg_hy)
arg_sab.add_postcondition(argpost_aonb,arg_hnc,arg_hy)
arg_sab.add_support(argpost_holda, arg_clearb)
arg_sac.add_postcondition(argpost_aonc,arg_hnc,arg_hy)
arg_sac.add_support(argpost_holda, arg_clearc)
arg_sad.add_postcondition(argpost_aond,arg_hnc,arg_hy)
arg_sad.add_support(argpost_holda, arg_cleard)
arg_unab.add_postcondition(argpost_holda, arg_clearb,arg_hnc,arg_hy)
arg_unab.add_support(argpost_aonb,arg_hc)
arg_unac.add_postcondition(argpost_holda, arg_clearc,arg_hnc,arg_hy)
arg_unac.add_support(argpost_aonc,arg_hc)
arg_unad.add_postcondition(argpost_holda, arg_cleard,arg_hnc,arg_hy)
arg_unad.add_support(argpost_aond)
arg_unscad.add_postcondition(argpost_holda, arg_cleard,arg_hnc,arg_hy)
arg_unscad.add_support(argpost_aond,arg_hy)
arg_unscab.add_postcondition(argpost_holda, arg_clearb,arg_hnc,arg_hy)
arg_unscab.add_support(argpost_aonb, arg_hy)
arg_unscac.add_postcondition(argpost_holda, arg_clearc,arg_hnc,arg_hy)
arg_unscac.add_support(argpost_aonc, arg_hy)
arg_puta.add_postcondition(arg_cleara,argpost_aontable,arg_hnc,arg_hy)
arg_puta.add_support(argpost_holda,arg_hc,arg_hy)

# Add supports and postconditions for the arguments

arg_pickb.add_postcondition(argpost_holdb)
arg_pickb.add_support(arg_clearb,arg_hc)
arg_pickscb.add_postcondition(argpost_holdb)
arg_pickscb.add_support(arg_hr)
arg_sba.add_postcondition(argpost_bona,arg_hnc,arg_hr)
arg_sba.add_support(argpost_holdb, arg_cleara)
arg_sbc.add_postcondition(argpost_bonc,arg_hnc,arg_hr)
arg_sbc.add_support(argpost_holdb, arg_clearc)
arg_sbd.add_postcondition(argpost_bond,arg_hnc,arg_hr)
arg_sbd.add_support(argpost_holdb, arg_cleard)
arg_unba.add_postcondition(argpost_holdb, arg_cleara,arg_hnc,arg_hr)
arg_unba.add_support(argpost_bona,arg_hc)
arg_unbc.add_postcondition(argpost_holdb, arg_clearc,arg_hnc,arg_hr)
arg_unbc.add_support(argpost_bonc)
arg_unbd.add_postcondition(argpost_holdb, arg_cleard,arg_hnc,arg_hr)
arg_unbd.add_support(argpost_bond,arg_cleanred,arg_hc)
arg_unscba.add_postcondition(argpost_holdb, arg_cleara,arg_hnc,arg_hr)
arg_unscba.add_support(argpost_bona, arg_hr)
arg_unscbc.add_postcondition(argpost_holdb, arg_clearc,arg_hnc,arg_hr)
arg_unscbc.add_support(argpost_bonc, arg_hr)
arg_unscbd.add_postcondition(argpost_holdb, arg_cleard,arg_hnc,arg_hr)
arg_unscbd.add_support(argpost_bona, arg_hr)
arg_putb.add_postcondition(arg_clearb, argpost_bontable,arg_hnc,arg_hr)
arg_putb.add_support(argpost_holdb,arg_hc,arg_hr)

arg_pickc.add_postcondition(argpost_holdc)
arg_pickc.add_support(arg_clearc,arg_hc)
arg_pickscc.add_postcondition(argpost_holdc)
arg_pickscc.add_support(arg_hr)
arg_sca.add_postcondition(argpost_cona)
arg_sca.add_support(argpost_holdc, arg_cleara)
arg_scb.add_postcondition(argpost_conb)
arg_scb.add_support(argpost_holdc, arg_clearb)
arg_scd.add_postcondition(argpost_cond)
arg_scd.add_support(argpost_holdc, arg_cleard)
arg_unca.add_postcondition(argpost_holdc, arg_cleara)
arg_unca.add_support(argpost_cona,arg_hc)
arg_uncb.add_postcondition(argpost_holdc, arg_clearb)
arg_uncb.add_support(argpost_conb)
arg_uncd.add_postcondition(argpost_holdc, arg_cleard)
arg_uncd.add_support(argpost_cond,arg_hc)
arg_unscca.add_postcondition(argpost_holdc, arg_clearb)
arg_unscca.add_support(argpost_cona, arg_hr,arg_hnc)
arg_unsccb.add_postcondition(argpost_holdc, arg_clearb)
arg_unsccb.add_support(argpost_conb, arg_hr)
arg_putc.add_postcondition(arg_clearc, argpost_contable,arg_hnc,arg_hr)
arg_putc.add_support(argpost_holdc,arg_hc,arg_hr)

arg_pickd.add_postcondition(argpost_holdd)
arg_pickd.add_support(arg_cleard,arg_cleanyellow)
arg_pickscd.add_postcondition(argpost_holdd)
arg_pickscd.add_support(arg_hy)
arg_sda.add_postcondition(argpost_dona,arg_hnc,arg_hy)
arg_sda.add_support(argpost_holdd, arg_cleara)
arg_sdb.add_postcondition(argpost_donb,arg_hnc,arg_hy)
arg_sdb.add_support(argpost_holdd, arg_clearb)
arg_sdc.add_postcondition(argpost_donc,arg_hnc,arg_hy)
arg_sdc.add_support(argpost_holdd, arg_clearc)
arg_unda.add_postcondition(argpost_holdd, arg_cleara,arg_hnc,arg_hy)
arg_unda.add_support(argpost_donb)
arg_undb.add_postcondition(argpost_holdd, arg_clearb,arg_hnc,arg_hy)
arg_undb.add_support(argpost_donb,arg_hc)
arg_undc.add_postcondition(argpost_holdd, arg_clearc,arg_hnc,arg_hy)
arg_undc.add_support(argpost_donc,arg_hc)
arg_unscad.add_postcondition(argpost_holdd, arg_cleara,arg_hnc,arg_hy)
arg_unscad.add_support(argpost_aond, arg_hy)
arg_putd.add_postcondition(arg_cleard, argpost_dontable,arg_hnc,arg_hy)
arg_putd.add_support(argpost_holdd,arg_hc,arg_hy)

arg_goal.add_support(argpost_aonb,argpost_bonc,argpost_cond)

arg_cleanred.add_postcondition(arg_hc)
arg_cleanred.add_support(arg_hnc,arg_hy)

arg_cleanyellow.add_postcondition(arg_hc)
arg_cleanyellow.add_support(arg_hnc,arg_hr)
#Add objects
# For Action Pick-up
arg_picka.add_objects(arg_a,arg_yellow)
arg_pickb.add_objects(arg_b,arg_red)
arg_pickc.add_objects(arg_c,arg_red)
arg_pickd.add_objects(arg_d,arg_yellow)

# For Action Pick-up Same Colour
arg_picksca.add_objects(arg_a,arg_yellow)
arg_pickscb.add_objects(arg_b,arg_red)
arg_pickscc.add_objects(arg_c,arg_red)
arg_pickscd.add_objects(arg_d,arg_yellow)

# For Stack actions
arg_sab.add_objects(arg_a, arg_b)
arg_sac.add_objects(arg_a, arg_c)
arg_sad.add_objects(arg_a, arg_d)
arg_sba.add_objects(arg_b, arg_a)
arg_sbc.add_objects(arg_b, arg_c)
arg_sbd.add_objects(arg_b, arg_d)
arg_sca.add_objects(arg_c, arg_a)
arg_scb.add_objects(arg_c, arg_b)
arg_scd.add_objects(arg_c, arg_d)
arg_sda.add_objects(arg_d, arg_a)
arg_sdb.add_objects(arg_d, arg_b)
arg_sdc.add_objects(arg_d, arg_c)

# For Unstack actions
arg_unab.add_objects(arg_a, arg_b,arg_yellow)
arg_unac.add_objects(arg_a, arg_c,arg_yellow)
arg_unad.add_objects(arg_a, arg_d,arg_yellow)
arg_unba.add_objects(arg_b, arg_a,arg_red)
arg_unbc.add_objects(arg_b, arg_c,arg_red)
arg_unbd.add_objects(arg_b, arg_d,arg_red)
arg_unca.add_objects(arg_c, arg_a,arg_red)
arg_uncb.add_objects(arg_c, arg_b,arg_red)
arg_uncd.add_objects(arg_c, arg_d,arg_red)
arg_unda.add_objects(arg_d, arg_a,arg_yellow)
arg_undb.add_objects(arg_d, arg_b,arg_yellow)
arg_undc.add_objects(arg_d, arg_c,arg_yellow)

# For Unstack Same Colour

arg_unscad.add_objects(arg_a, arg_d,arg_yellow)
arg_unscbc.add_objects(arg_b, arg_c,arg_red)
arg_unsccb.add_objects(arg_c, arg_b,arg_red)
arg_unscda.add_objects(arg_d, arg_a,arg_yellow)


# For Put-down actions
arg_puta.add_objects(arg_a,arg_yellow)
arg_putb.add_objects(arg_b,arg_red)
arg_putc.add_objects(arg_c,arg_red)
arg_putd.add_objects(arg_d,arg_yellow)

# For Clean action
arg_cleanred.add_objects(arg_red)
arg_cleanyellow.add_objects(arg_yellow)

# For Postconditions
argpost_aonb.add_objects(arg_a, arg_b)
argpost_aonc.add_objects(arg_a, arg_c)
argpost_aond.add_objects(arg_a, arg_d)
argpost_bona.add_objects(arg_b, arg_a)
argpost_bonc.add_objects(arg_b, arg_c)
argpost_bond.add_objects(arg_b, arg_d)
argpost_cona.add_objects(arg_c, arg_a)
argpost_conb.add_objects(arg_c, arg_b)
argpost_cond.add_objects(arg_c, arg_d)
argpost_dona.add_objects(arg_d, arg_a)
argpost_donb.add_objects(arg_d, arg_b)
argpost_donc.add_objects(arg_d, arg_c)

# For Holding postconditions
argpost_holda.add_objects(arg_a)
argpost_holdb.add_objects(arg_b)
argpost_holdc.add_objects(arg_c)
argpost_holdd.add_objects(arg_d)

# For On table postconditions
argpost_aontable.add_objects(arg_a)
argpost_bontable.add_objects(arg_b)
argpost_contable.add_objects(arg_c)
argpost_dontable.add_objects(arg_d)

# For Clear conditions
arg_cleara.add_objects(arg_a)
arg_clearb.add_objects(arg_b)
arg_clearc.add_objects(arg_c)
arg_cleard.add_objects(arg_d)




pruned_list1 = prune_list(present_arguments1,index)
#print(pruned_list1)
results1 = check_postconditions_supporting_arguments(selected_arg, pruned_list1)
# print(f"results1 {results1}")
# for result in results1:
#     print(f"Postcondition {result[1].name} of argument {selected_arg.name} supports argument {result[0]}")

set_chosen(results1, arguments)
if selected_arg.show_objects:
    set_objects_chosen(selected_arg)

if replacement == True:
    pruned_list2 = prune_list(present_arguments2,index)
    #print(pruned_list2)
    results2 = check_postconditions_supporting_arguments(replacement_arg, present_arguments2)
    # print(f"results2 {results2}")
    # for result in results2:
    #     print(f"Postcondition {result[1].name} of argument {replacement_arg.name} supports argument {result[0]}")
    set_chosen(results2, arguments)
    if replacement_arg.show_objects:
        set_objects_chosen(replacement_arg)


chosen_argument_names,chosen_arguments = list_chosen_arguments(arguments)
# print("Chosen arguments:", chosen_argument_names)

print(f"The origial cost of the plan is {cost1} and the cost of the new plan is {cost2}\n")
exp = int(input("Enter '1' to see the line of reasoning for the change in cost:"))
if exp==1:
    graph = create_argument_graph(chosen_arguments)
    visualize_argument_graph(graph)
    display_plans(plan1,plan2)


