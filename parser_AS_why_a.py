import os
import re

# Changes the name of the domain and the problem file
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
        else:
            match = re.search(rf'\b{keyword}\s+(\w+)\)', line)
            if match:
                new_name = f'new{match.group(1)}'
                line = line.replace(match.group(1), new_name)
        modified_lines.append(line)
        i += 1
    return modified_lines

# Extracts the paramerts of the action required to add the increase effect
def extract_action_parameters(domain_lines, action_name):
    parameters = None
    action_start = None
    action_depth = 0

    for i, line in enumerate(domain_lines):
        if f'(:action {action_name}' in line.strip():
            print(f"Found action {action_name} at line {i}: {line.strip()}")
            action_start = i
            action_depth = 1
        elif action_start is not None:
            action_depth += line.count('(') - line.count(')')
            if line.strip().startswith(':parameters'):
                match = re.search(r'\:parameters\s*\((.*?)\)', line)
                if match:
                    parameters = match.group(1).strip()
                    print(f"Extracted parameters for action {action_name}: {parameters}")
            if action_depth == 0:
                break

    return parameters

# Adds increase effect to action and adds a functions section to the domain
def add_counter_to_action(domain_file, action_name, counter_name, new_domain_file):
    if os.path.exists(new_domain_file):
        os.remove(new_domain_file)

    with open(domain_file, 'r') as file:
        domain_lines = file.readlines()

    requirements_found = False
    for i, line in enumerate(domain_lines):
        if line.strip().startswith('(:requirements'):
            requirements_found = True
            if ':numeric-fluents' not in line:
                line = line.strip().rstrip(')') + ' :numeric-fluents)\n'
            domain_lines[i] = line
            break

    if not requirements_found:
        raise ValueError("The requirements section is missing in the domain file.")

    parameters_line = extract_action_parameters(domain_lines, action_name)
    if not parameters_line:
        raise ValueError(f"Action {action_name} not found in the domain file.")

    params = parameters_line

    action_start_line = None
    for i, line in enumerate(domain_lines):
        if line.strip().startswith('(:action'):
            action_start_line = i
            break

    if action_start_line is not None:
        domain_lines.insert(action_start_line, '(:functions\n')
        domain_lines.insert(action_start_line + 1, f'    ({counter_name} {params})\n')
        domain_lines.insert(action_start_line + 2, ')\n')

    action_start = None
    action_end = None
    action_depth = 0

    for i, line in enumerate(domain_lines):
        if f'(:action {action_name}' in line.strip():
            action_start = i
            action_depth = 1
        elif action_start is not None:
            action_depth += line.count('(') - line.count(')')
            if action_depth == 0:
                action_end = i
                break

    if action_start is not None and action_end is not None:
        effect_start = None
        for i in range(action_start, action_end + 1):
            if domain_lines[i].strip().startswith(':effect'):
                effect_start = i+1
                break

        if effect_start is not None:
            domain_lines.insert(effect_start + 1, f'  (increase ({counter_name} ' + ' '.join(
                param.strip() for param in params.split() if param.startswith('?')) + ') 1)\n')

    modified_domain_lines = modify_line(domain_lines, 'domain')

    with open(new_domain_file, 'w') as file:
        file.writelines(modified_domain_lines)
    print(f"Domain file updated and saved as {new_domain_file}")

# Adds action_counter to the goal. Setting the curret value to 0 and adding a limit on the number of actions
def add_goal_condition(problem_file, counter_name, variables, threshold, new_problem_file):
    if os.path.exists(new_problem_file):
        os.remove(new_problem_file)

    with open(problem_file, 'r') as file:
        problem_lines = file.readlines()

    counter_initial = f'(= ({counter_name} ' + ' '.join(f'{var}' for var in variables) + ') 0)'
    if not any(counter_initial in line for line in problem_lines):
        init_start = None
        init_end = None
        init_depth = 0
        for i, line in enumerate(problem_lines):
            if line.strip().startswith('(:init'):
                init_start = i
                init_depth = 0
            if init_start is not None:
                init_depth += line.count('(') - line.count(')')
                if init_depth == 0:
                    init_end = i
                    break
        if init_start is not None and init_end is not None:
            problem_lines.insert(init_end, f'    {counter_initial}\n')

    goal_start = None
    goal_end = None
    goal_depth = 0
    for i, line in enumerate(problem_lines):
        if line.strip().startswith('(:goal'):
            goal_start = i
            goal_depth = 0
        if goal_start is not None:
            goal_depth += line.count('(') - line.count(')')
            if goal_depth == 0:
                goal_end = i
                break

    counter_goal_condition = f'(< ({counter_name} ' + ' '.join(f'{var}' for var in variables) + f') {threshold})'
    if goal_start is not None and goal_end is not None:
        if not any(counter_goal_condition in line for line in problem_lines[goal_start:goal_end]):
            for i in range(goal_start, goal_end + 1):
                if problem_lines[i].strip().startswith('(and') or problem_lines[i].strip().startswith('( and') or problem_lines[i].strip().startswith('('):
                    insert_position = i + 2
                    problem_lines.insert(insert_position, f'    {counter_goal_condition}\n')
                    break

    modified_problem_lines = modify_line(problem_lines, 'problem')
    modified_problem_lines = modify_line(modified_problem_lines, 'domain')

    with open(new_problem_file, 'w') as file:
        file.writelines(modified_problem_lines)
    print(f"Problem file updated and saved as {new_problem_file}")

def process_pddl_A(domain_file, problem_file, action_with_vars, threshold, new_domain_file, new_problem_file):
    action_name, *variables = action_with_vars.split()
    print(f"Action is {action_name}")
    add_counter_to_action(domain_file, action_name, "action_counter", new_domain_file)
    add_goal_condition(problem_file, "action_counter", variables, threshold, new_problem_file)