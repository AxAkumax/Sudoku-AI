import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking ( self ):
        #Eliminate values for assigned neighbors
        UncheckedAssignedValues = []
        variable_dict = {}

        #Get all assigned values
        for i in self.network.variables:
            if i.isAssigned():
                UncheckedAssignedValues.append(i)

        #Update values inside
        while len(UncheckedAssignedValues)!=0:
            i = UncheckedAssignedValues.pop()
            #Get assigned value neighbors
            neighbors = self.network.getNeighborsOfVariable(i)
            #Update by eliminating option of neighbors
            for j in neighbors:
                if not j.isAssigned() and j.isChangeable() and j.getDomain().contains(i.getAssignment()):

                    #Push to trail then modify
                    self.trail.push(j)
                    j.removeValueFromDomain(i.getAssignment())
                    variable_dict[j] = j.getDomain()

                    #Assign value if possible
                    if(j.size() == 1):
                        self.trail.push(j)
                        #x = j.getValues()
                        j.assignValue(j.domain.values[0])
                        UncheckedAssignedValues.append(j)
                    
                    #We know something is not consistent so return 0
                    if j.size() == 0:
                        return (variable_dict, False)
            
        
        return (variable_dict, self.network.isConsistent())

    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        #First part of Norvig is just implementing Forward Checking
        #-------------------------------------------------------------------------------------
        #Eliminate values for assigned neighbors
        variable_dict = {}

        #If variable is assigned, then eleminate that value from the square's neighbors
        for i in self.network.variables:
            if i.isAssigned():
                for j in self.network.getNeighborsOfVariable(i):
                    if not j.isAssigned() and j.isChangeable() and j.getDomain().contains(i.getAssignment()):
                         self.trail.push(j)
                         j.removeValueFromDomain(i.getAssignment())
                         #If a constraint has only one possible place for a value then put the value there.
                         if j.size() == 1:
                            self.trail.push(j)
                            variable_dict[j] = j.domain.values[0]
                            j.assignValue(j.domain.values[0])
                
        return (variable_dict, self.network.isConsistent())

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return self.norvigCheck()

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):

        size = len(self.network.constraints)
        smallest=None

        for i in self.network.variables:
            if i.isAssigned() == False:
                if i.size()<= size:
                    size = i.size()
                    smallest = i
       
        return smallest

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):

        smallest = self.getMRV()
        if smallest == None:
            return [None]
        
        #filters all of the variables from network that don't have the smallest domain
        vars = []
        for i in self.network.variables:
            if i.isAssigned() == False and i.size()<=smallest.size():
                vars.append(i)
        degree_vars = {}
        
        #make a dictionary of the variable with its degree (key = variable : value = degree)
        for i in vars:
            j = self.network.getNeighborsOfVariable(i)
            unassigned_neighbors = []
            for n in j:
                if n.isAssigned() == False:
                    unassigned_neighbors.append(n)
            degree_vars[i] = len(unassigned_neighbors)
        #find the variable with the largest number of unassigned neighbors
        size = 0
        largest_degree = None
        for i in degree_vars.keys():
            if degree_vars[i] >= size:
                size = degree_vars[i]
                largest_degree = i

         #add all the largest degrees to a list
        degree_list = []
        for i in degree_vars:
            if degree_vars[i]==size:
                degree_list.append(i)
        #if the list is greater than 1, add the variables to the network
        if len(degree_list) > 1:
            for i in degree_list:
                self.network.addVariable(i)
        #what if the list is 0?? IndexError
        
        return degree_list

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return self.MRVwithTieBreaker()[0]

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        #get neighbors of Variable V
        neighbors= self.network.getNeighborsOfVariable(v)

        #dictionary to tally up all the occurances of a value in Variable v's neighbors" domain
        value_order = {} 
        values = v.getValues()
        for i in values:
            value_order[i] = 1
        
        for i in neighbors:
            if i.isAssigned() == False:
                domain_val = i.getValues()
                for d in domain_val:
                    if d in value_order:
                        value_order[d]+=1
                   
       
        #sorts all the keys by value in dictionary and returns a list
        pair_list = sorted(value_order.items(), key = lambda x: x[1], reverse = False)
        lcv_sorted = []
        for i, j in pair_list:
            lcv_sorted.append(i)
        
        return lcv_sorted

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return self.getValuesLCVOrder(v)

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
