import os
import subprocess
import re
import pyautogui
import time
import random

# Main function to create .plan and .happenings files
def create_files(res, file_name):
    names, domain_file, problem_file = extract_name(file_name)
    
    try:

        if res.returncode == 0:
            # Extract directory from file_name
            dir_name = os.path.dirname(domain_file)
            print(dir_name)
            plan_file_name = None
            for f in os.listdir(dir_name):
                if f.endswith('.plan'):
                    os.remove(os.path.join(dir_name, f))

            
            file_num = random.randint(0,10000)
            # Create a new .plan file
            plan_file_name = f'plan{file_num}.plan'
            planfile = os.path.join(dir_name,plan_file_name )
            
            # Write the output to the new file
            with open(planfile, 'w') as file:
                file.write(names)
                file.write(res.stdout)
            print(f"Plan saved to {planfile}")
            plan_to_happenings(planfile, domain_file,problem_file)
        else:
            print("Error running POPF:")
            print(res.stderr)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    pyautogui.hotkey('ctrl', 'shift', 'E')
    os.system(f"code {AS}")

def planner(file_name,nn):
    command = file_name
    res = subprocess.run(command, capture_output=True, text=True, shell=True)
    plan = res.stdout
    error = res.stderr
    
    if "Solution Found" in plan:
        if nn:
            create_files(res,file_name)
        cost_match = re.search(r"; Cost: ([\d.]+)", plan)
        if cost_match:
            cost = float(cost_match.group(1))
        else:
            cost = None

        cost_index = plan.find("; Cost:")
        if cost_index != -1:
            output_after_cost = plan[cost_index:].split("\n", 1)[1]
        else:
            output_after_cost = ""

    elif "Problem unsolvable!" in plan:
        return "not solvable", float('inf')
    else:
        return "Internal error in planner", -1
    
    return output_after_cost, cost

def action_list(plansteps,durative):
    # Parse and clean the actions
    lines = plansteps.strip().split("\n")
    actions = []
    durative_times= []
    for line in lines:
        # Extract the action part of the line
        parts = line.split(":", 1) 
        if len(parts) > 1:
            if durative:
                action_part = parts[1].strip()
                action_start = action_part.find('(')
                action_end = action_part.find(')')
                if action_start != -1 and action_end != -1:
                    action = action_part[action_start + 1:action_end].strip()
                    
                    # Extract the time value enclosed in square brackets
                    time_start = action_part.find('[')
                    time_end = action_part.find(']')
                    if time_start != -1 and time_end != -1:
                        time_value = action_part[time_start + 1:time_end].strip()
                        actions.append(action)
                        durative_times.append( time_value)
                
            else:
                action = parts[1].strip()
                actions.append(action)

    return actions,durative_times

# Extract names to create the .plan file
def extract_name(file_name):
    parts = file_name.split()
    
    if len(parts) < 3:
        raise ValueError("Command does not have enough parts to extract file paths")
    
    domain_file = parts[1]
    problem_file = parts[2]

    # Extract domain name from the domain file
    with open(domain_file, 'r') as file:
        domain_content = file.read()
        domain_match = re.search(r'\(define \(domain (\w+)\)', domain_content)
        domain_name = domain_match.group(1) if domain_match else "UnknownDomain"

    # Extract problem name from the problem file
    with open(problem_file, 'r') as file:
        problem_content = file.read()
        problem_match = re.search(r'\(define \(problem (\w+)\)', problem_content)
        problem_name = problem_match.group(1) if problem_match else "UnknownProblem"

    extracted_names = f";;!domain:{domain_name}\n;;!problem:{problem_name}\n"
    print(extracted_names)
    clean_directory(os.path.dirname(domain_file), domain_file, problem_file)
    return extracted_names, domain_file, problem_file

# Creating a .happenings file
def plan_to_happenings(file_path, domain_file,problem_file):

    # Visit domain file and problem file to register the files and aviod PDDL extension bug 
    os.system(f"code {domain_file}")
    time.sleep(0.1)
    os.system(f"code {problem_file}")
    time.sleep(0.1) 

    # Open the specified happenings file in VSCode
    os.system(f"code {file_path}")
    time.sleep(0.3)  

    # Open the Command Palette
    pyautogui.hotkey('ctrl', 'shift', 'p')
    time.sleep(0.3)

    # Convert to .happenings file
    pyautogui.write('PDDL: Convert plan to happenings')
    time.sleep(0.3)
    pyautogui.press('enter')

    wait_to_save(os.path.dirname(file_path), ".happenings")

    happenings_file = find_file(os.path.dirname(file_path), ".happenings")
    if happenings_file:
        print(f"Happenings saved to {happenings_file}")
        plan_states(happenings_file, domain_file,problem_file)
    else:
        print("Happenings file not found.")

#Function to wait until the file has been saved
def wait_to_save(directory, extension):
    print("Please save the file in the popup window.")
    while True:
        file_path = find_file(directory, extension)
        if file_path:
            break
        time.sleep(1)
    time.sleep(1) 

#Function to find a specific file
def find_file(directory, extension):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                return os.path.join(root, file)
    return None

# Remove all files in the directory except the domain and problem files
def clean_directory(directory, domain_file, problem_file):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file != os.path.basename(domain_file) and file != os.path.basename(problem_file):
                os.remove(os.path.join(root, file))
                print(f"Removed file: {os.path.join(root, file)}")

def plan_states(step_path, domain_file,problem_file):
 
    # Visit domain file and problem file to register the files and aviod PDDL extension bug
    os.system(f"code {domain_file}")
    time.sleep(0.1)  
    os.system(f"code {problem_file}")
    time.sleep(0.1)  

    os.system(f"code {step_path}")
    time.sleep(0.3)  

    pyautogui.hotkey('ctrl', 'shift', 'p')
    time.sleep(0.3)

    # Type the PDDL command
    pyautogui.write('PDDL: Execute plan and generate plan-resume test cases')
    time.sleep(0.3)
    pyautogui.press('enter')


    wait_to_save(os.path.dirname(step_path), ".ptest.json")


AS = 'D:/aip/AS.py'
