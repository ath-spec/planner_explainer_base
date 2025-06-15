import os
import re
import shutil
from collections import deque

#function used to modify the names of the new domian and problem
def modify_line(lines, keyword): 
    modified_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.search(rf'\b{keyword}\s*$', line)  
        if match:
            next_line = lines[i + 1].strip()  
            new_name = f'new{next_line.split()[0]}'
            lines[i + 1] = lines[i + 1].replace(next_line.split()[0], new_name)
            print(line)
        else:
            match = re.search(rf'\b{keyword}\s+(\w+)\)', line)
            if match:
                new_name = f'new{match.group(1)}'
                new_name = new_name.lower()
                line = line.replace(match.group(1), new_name)
                print(line)
        modified_lines.append(line)
        i += 1
    return modified_lines

#Function used to extract parameters to apply grounded transformations
def extract_action_parameters(domain_lines, action_name,durative): 
    parameters = None
    action_start = None
    action_depth = 0
    if durative== True:
            action_syntax = '(:durative-action'
    else:
        action_syntax = '(:action'
    for i, line in enumerate(domain_lines):
        if f'{action_syntax} {action_name}' in line.strip():
            action_start = i
            action_depth = 1
        elif action_start is not None:
            action_depth += line.count('(') - line.count(')')
            if line.strip().startswith(':parameters'):
                match = re.search(r'\:parameters\s*\((.*?)\)', line)
                if match:
                    parameters = match.group(1).strip()
            if action_depth == 0:
                break

    return parameters

# Adding modifying the action in the domain to add effect done_action_{b}
def add_done_action_to_domain(action_name, new_domain_file,durative):

    with open(new_domain_file, 'r') as file:
        domain_lines = file.readlines()

    parameters_line = extract_action_parameters(domain_lines, action_name,durative)
    if not parameters_line:
        raise ValueError(f"Action {action_name} not found in the domain file.")

    params = parameters_line.strip()

    done_action_predicate = f'(done_action_{action_name} {parameters_line})'
    predicates_start = None
    predicates_end = None
    predicates_depth = 0

    for i, line in enumerate(domain_lines):
        if line.strip().startswith('(:predicates'):
            predicates_start = i
            predicates_depth = 1
        elif predicates_start is not None:
            predicates_depth += line.count('(') - line.count(')')
            if predicates_depth == 0:
                predicates_end = i
                break

    if predicates_start is not None and predicates_end is not None:
        predicates_section = domain_lines[predicates_start:predicates_end]
        predicate_present = any(done_action_predicate in line for line in predicates_section)

        if not predicate_present:
            new_predicates = predicates_section + [f'    {done_action_predicate}\n']
            domain_lines[predicates_start:predicates_end] = new_predicates

    action_start = None
    action_end = None
    action_depth = 0
    effect_start = None
    if durative== True:
            action_syntax = '(:durative-action'
    else:
        action_syntax = '(:action'
    for i, line in enumerate(domain_lines):
        if f'{action_syntax} {action_name}' in line.strip():
            action_start = i
            action_depth = 1
        elif action_start is not None:
            action_depth += line.count('(') - line.count(')')
            if line.strip().startswith(':effect'):
                effect_start = i
            if action_depth == 0:
                action_end = i
                break

    if effect_start is not None:
        effect_end = action_end if action_end is not None else len(domain_lines)
        effect_lines = domain_lines[effect_start:effect_end]
        if durative== True:
            done_action_effect = f'(at end (done_action_{action_name} ' + ' '.join(
                param.strip() for param in params.split() if param.startswith('?')) + '))\n'
        else:
            done_action_effect = f'  (done_action_{action_name} ' + ' '.join(
                param.strip() for param in params.split() if param.startswith('?')) + ')\n'

        new_effect_lines = [line for line in effect_lines]  
        if len(new_effect_lines) >= 2:
            new_effect_lines.insert(2, done_action_effect)  
        else:
            new_effect_lines.append(done_action_effect)

        domain_lines[effect_start:effect_end] = new_effect_lines

    modified_domain_lines = modify_line(domain_lines, 'domain')

    with open(new_domain_file, 'w') as file:
        file.writelines(modified_domain_lines)
    print(f"Domain file updated and saved as {new_domain_file}")

# Adding modifying the goal to perform action 'b' by adding done_action_{b}
def add_goal_condition(action_name, variables, new_problem_file, durative):

    def find_section_indices(lines, start_str):
        start_idx = None
        end_idx = None
        depth = 0
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith(start_str):
                if start_idx is None:
                    start_idx = i
                depth += stripped_line.count('(') - stripped_line.count(')')
                if depth == 0:
                    end_idx = i
                    break
        return start_idx, end_idx

    with open(new_problem_file, 'r') as file:
        problem_lines = file.readlines()

    goal_start, goal_end = find_section_indices(problem_lines, '(:goal')
    metric_start, metric_end = find_section_indices(problem_lines, '(:metric')

    if goal_start is not None:
        if goal_end is None:
            goal_end = len(problem_lines) - 1
        
        if metric_start is not None and metric_end is not None:
            if goal_end < metric_start:

                problem_lines = problem_lines[:goal_start] + problem_lines[metric_end + 1:]
            else:
                problem_lines = problem_lines[:goal_start] + problem_lines[goal_end + 1:]
        else:
            problem_lines = problem_lines[:goal_start] + problem_lines[goal_end + 1:]

    goal_condition = f'(:goal (and (done_action_{action_name} ' + ' '.join(f'{var}' for var in variables) + ')))\n)'
    problem_lines.append(goal_condition)

    with open(new_problem_file, 'w') as file:
        file.writelines(problem_lines)
    
    modified_problem_lines= modify_line(problem_lines, 'domain')

    with open(new_problem_file, 'w') as file:
        file.writelines(modified_problem_lines)
    print(f"Problem file updated and saved as {new_problem_file}")

#Function to copy the transitional to new domain and problem. 
# Transitional domain file referes to the file initial state post the execution of action a_{i-1}
def copy_files(domain_file_path, problem_file_path, old_arg, arg2, time_number, new_domain_file, new_problem_file,durative,when,index):
    old_arg = old_arg.replace(' ', '_')

    folder_path = os.path.dirname(domain_file_path)
    base_problem_file_name = os.path.splitext(os.path.basename(problem_file_path))[0]
    time_number = float(time_number)
    if time_number ==0.0:
        time_number = 0
    if index !=0 or time_number!=-1:
        print("Case 1")
        if durative ==True:
            transition_prob_file_name = f"{base_problem_file_name}_{time_number}_{old_arg}_{when}.pddl"
            transition_prob_file_path = os.path.join(folder_path, transition_prob_file_name)
        else:
            transition_prob_file_name = f"{base_problem_file_name}_{time_number}_{old_arg}.pddl"
            transition_prob_file_path = os.path.join(folder_path, transition_prob_file_name)
    elif index==0 and time_number==-1:
        print("Case 2")
        transition_prob_file_name = f"{base_problem_file_name}.pddl"
        transition_prob_file_path = os.path.join(folder_path, transition_prob_file_name)

    new_domain_dir = os.path.dirname(new_domain_file)
    new_problem_dir = os.path.dirname(new_problem_file)
    os.makedirs(new_domain_dir, exist_ok=True)
    os.makedirs(new_problem_dir, exist_ok=True)

    if os.path.exists(new_domain_file):
        os.remove(new_domain_file)
    if os.path.exists(new_problem_file):
        os.remove(new_problem_file)

    print(f"Transition Problem File Path: {transition_prob_file_path}")

    if os.path.isfile(transition_prob_file_path):
        print("Transition File found")
        source_problem_file_path = transition_prob_file_path
    else:
        source_problem_file_path = problem_file_path
    
    print(f"Source File Path: {source_problem_file_path}")

    shutil.copyfile(source_problem_file_path, new_problem_file)
    shutil.copyfile(domain_file_path, new_domain_file)
    return new_domain_file, new_problem_file


def process_pddl_AB1(domain_file, problem_file, old_arg, new_arg, time_number, new_domain_file, new_problem_file,durative,when,index):
    action_name, *variables = new_arg.split() # Here the varibles are the predicates of the action 
    print(f"Action is {action_name}")

    new_domain_file,new_problem_file= copy_files(domain_file, problem_file, old_arg, new_arg, time_number, new_domain_file, new_problem_file,durative,when,index)
    add_done_action_to_domain(action_name, new_domain_file,durative)
    add_goal_condition(action_name, variables, new_problem_file,durative)