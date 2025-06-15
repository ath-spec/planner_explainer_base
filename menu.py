def selection(plan,args):

    print(f"Plan to solve problem:\n{plan}")
    rep = int(input("Questions:\nQ1: Why action A?\nQ2: Why action A and not B?\nEnter enter type of question (1/2):"))
    ind = int(input("Enter index of action A:"))
    arg = args[ind]
    if rep ==1:
        return arg,ind,False
    elif rep==2:
        return arg,ind,True
    
    

def rep_selection(arguments):

    while True:
        rname = str(input("Enter complete name of action B:"))
        for rarg in arguments:
            if rname == rarg.name:
                reparg = rarg
                break
        if reparg:
            break
        else:
            raise ValueError("No such action found in domain")
    return reparg