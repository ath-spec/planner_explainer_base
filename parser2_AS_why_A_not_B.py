import os
import re

# Removes the goal section from the transitional file where action 'b' has been executed
def remove_goal_section(file_lines):
    file_content = ''.join(file_lines)
    pattern = r'\(:goal\s*\(.*?\)\)*'
    new_content = re.sub(pattern, '', file_content, flags=re.DOTALL)
    return new_content.splitlines(True)

# Extracts the goal section form the original problem file. Also Extracts metric section if present.
def extract_section(file_lines,durative):

    file_content = ''.join(file_lines)
    metric_section = ''
    goal_section = ''
    if durative:
        metric_start = file_content.find('(:metric')
        if metric_start != -1:
            metric_end = file_content.find(')', metric_start) + 1
            metric_section = file_content[metric_start:metric_end].strip()
    
    goal_start = file_content.find('(:goal')
    if goal_start != -1:
        goal_end = file_content.find('))', goal_start) + 1
        goal_section = file_content[goal_start:goal_end].strip()
    
    if durative:
        if metric_section and goal_section:
            return metric_section + ')\n' + goal_section +')'
        elif metric_section:
            return metric_section
        elif goal_section:
            return goal_section  +')'
        else:
            return ''
    else:
        if goal_section:
            return goal_section +')\n)'
        else:
            return ''

# Extracts the goal section form the original problem file
def extract_goal_section(file_lines):
    file_content = ''.join(file_lines)
    pattern = r'\(:goal\s*\(.*?\)\)\s*\)'
    matches = re.findall(pattern, file_content, flags=re.DOTALL)
    
    if matches:
        return matches[0]
    else:
        return '' 

# Copy original domain to new domain and update new problem file with 
# combined goal and initial state from original problem and transitional problem where 'b' has been executed
def update_problem_file(original_problem_file_path, transition_prob_file_path, new_problem_file_path,durative):

    if os.path.isfile(transition_prob_file_path):
        with open(transition_prob_file_path, 'r') as file:
            transition_prob_lines = file.readlines()
    else:
        raise FileNotFoundError(f"Transition problem file not found: {transition_prob_file_path}")


    with open(original_problem_file_path, 'r') as file:
        original_problem_lines = file.readlines()
 
    original_goal_section = extract_section(original_problem_lines,durative)
    filtered_prob_lines = remove_goal_section(transition_prob_lines)
    
    
    with open(new_problem_file_path, 'w') as file:
        file.writelines(filtered_prob_lines)
        if original_goal_section:
            file.write(original_goal_section)
    
    print(f"Transition Problem File Path: {transition_prob_file_path}")
    print(f"Original Problem File Path: {original_problem_file_path}")
    print(f"New Problem File Path: {new_problem_file_path}")

#Applies transformation to domain and problem file after executing b
def process_pddl_AB2(original_problem_file, old_arg, time_number, new_problem_file,durative,when,prev_time):
    folder_path = os.path.dirname(new_problem_file)
    print(f"folder path {folder_path}")
    new_base_problem_file_name = os.path.splitext(os.path.basename(new_problem_file))[0]
    print(f"base name {new_base_problem_file_name}")
    if time_number ==0.0:
        time_number = 0
    if durative == True:
        transition_prob_file_name = f"{new_base_problem_file_name}_{time_number}_{old_arg.replace(' ', '_')}_{when}.pddl"
        transition_prob_file_path = os.path.join(folder_path, transition_prob_file_name)
    else:
        transition_prob_file_name = f"{new_base_problem_file_name}_{time_number}_{old_arg.replace(' ', '_')}.pddl"
        transition_prob_file_path = os.path.join(folder_path, transition_prob_file_name)
        print(f"Transition Problem File Path: {transition_prob_file_path}")
    update_problem_file(original_problem_file, transition_prob_file_path, new_problem_file,durative)