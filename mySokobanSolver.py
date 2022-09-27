
'''

    Sokoban assignment


The functions and classes defined in this module will be called by a marker script. 
You should complete the functions and classes according to their specified interfaces.

No partial marks will be awarded for functions that do not meet the specifications
of the interfaces.

You are NOT allowed to change the defined interfaces.
In other words, you must fully adhere to the specifications of the 
functions, their arguments and returned values.
Changing the interfacce of a function will likely result in a fail 
for the test of your code. This is not negotiable! 

You have to make sure that your code works with the files provided 
(search.py and sokoban.py) as your code will be tested 
with the original copies of these files. 

Last modified by 2022-03-27  by f.maire@qut.edu.au
- clarifiy some comments, rename some functions
  (and hopefully didn't introduce any bug!)

'''

# You have to make sure that your code works with 
# the files provided (search.py and sokoban.py) as your code will be tested 
# with these files

import search 
from sokoban import Warehouse


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def my_team():
    '''
    Return the list of the team members of this assignment submission as a list
    of triplet of the form (student_number, first_name, last_name)
    
    '''
    return [ (10923543,'Ye Gaung','Kyaw')]
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -



class SokobanPuzzle(search.Problem):
    '''
    An instance of the class 'SokobanPuzzle' represents a Sokoban puzzle.
    An instance contains information about the walls, the targets, the boxes
    and the worker.

    Your implementation should be fully compatible with the search functions of 
    the provided module 'search.py'. 
    
    '''
    
    #
    #         "INSERT YOUR CODE HERE"
    #
    #     Revisit the sliding puzzle and the pancake puzzle for inspiration!
    #
    #     Note that you will need to add several functions to 
    #     complete this class. For example, a 'result' method is needed
    #     to satisfy the interface of 'search.Problem'.
    #
    #     You are allowed (and encouraged) to use auxiliary functions and classes

    def __init__(self, warehouse,taboocells = None):
        assert isinstance(warehouse,Warehouse)              
        self.warehouse =warehouse
        #dynamic
        self.initial = self.warehouse_to_state(warehouse)          
        #extra
        if taboocells:
            self.taboocells = taboocells
        else:
            self.taboocells = find_taboo_cells(warehouse)

    def warehouse_to_state(self,warehouse: Warehouse) -> list:
        '''
        Covert the warehouse to State (tuple)

        Params:
            - warehouse : warehouse

        Returns:
            - Tuple of Coordinates ( Worker and Boxes)

        '''
        state = []
        state.append(warehouse.worker)
        state.append(tuple(warehouse.boxes))
        return tuple(state)

    def state_to_warehouse(self,state: tuple) -> Warehouse:
        '''
        Covert the State to Warehouse

        Params:
            - state : current state

        Returns:
            - warehouse object with current state
        ''' 
        return self.warehouse.copy(state[0],state[1])

    
    def goal_test(self, state:tuple) -> bool:        
        '''
        Check if the current state is goal state
        
        Params:
            - state : current state

        Return:
            true if all boxes are in targets cells.
        '''            
        # True means coordinates of boxes == corrdinates of targers
        return set(state[1])==set(self.warehouse.targets)

    def actions(self, state:tuple) -> list:
        """
        Return the list of legal actions that can be executed in the given state.
        
        Params:
            - state : current state
        
        Return:
            List of legal actions. ("Up" , "Down" , "Left" , "Right")
        """
        wh = self.state_to_warehouse(state)
        L = []  # list of legal actions
        
        wh = self.warehouse.copy(state[0],state[1])

        if  self.is_move_legal(wh,'Up'):
            L.append('Up')
        if  self.is_move_legal(wh,'Down'):
            L.append('Down')
        if  self.is_move_legal(wh,'Left'):
            L.append('Left')
        if  self.is_move_legal(wh,'Right'):
            L.append('Right')     
        return L

    #similar to check_elem_action_seq  // see BELOW
    #but use for finding an action for one move, not updating the result
    # move will be from one of "Left" "Right" "Up" or "Down"
    # return type will be boolean

    def is_move_legal(self, warehouse : Warehouse, move : str) -> bool:
        '''
        Check whether the move is legal or not.

        Illegal List
            - When the player is trying to move into a wall
            - When the player is trying to push a box into a wall
            - When the player is trying to push a box into an another box.
            - When the player is trying to push a box into a taboo cells.

        Params:
            - warehouse:  warehouse in current state
            - move : action that is currently executing

        Returns:
            True if the move is legal.
        '''

        deltaDir = direction(move)
        attemptCoor = move_towards(warehouse.worker,deltaDir)

        #Return False means Invalid Moves
        if(is_coordinate_wall(warehouse,attemptCoor)): # if it bumps into a wall 
            return False
        elif(is_coordinate_box(warehouse,attemptCoor)): # if it bumps into a box. Need to check more.
            if(is_coordinate_wall(warehouse,move_towards(attemptCoor,deltaDir))):  # if a tile ahead is a wall.
                return False
            elif(is_coordinate_box(warehouse,move_towards(attemptCoor,deltaDir))): # if a tile ahead is another box.
                return False
            elif( move_towards(attemptCoor,deltaDir) in self.taboocells ): # if a tile ahead is taboo cell
                return False

        return True


    def result(self, state : tuple, action : str) -> tuple:
        '''
        Return the state that results from executing the given action in the given state.
        The action must be one of self.actions(state).

        Params:
            state : state before the action
            action: direction for the worker to move

        Returns:
            the new state        

        '''
        wh = self.state_to_warehouse(state)

        deltaDir = direction(action)
        attemptCoor = move_towards(wh.worker,deltaDir)

        if(is_coordinate_box(wh,attemptCoor)): # if it bumps into a box. 
            wh.boxes = list(wh.boxes)
            for i,boxCor in enumerate(wh.boxes):
                if(boxCor == attemptCoor ):
                    wh.boxes.pop(i) # remove that box 
                    wh.boxes.insert(i,move_towards(attemptCoor,deltaDir)) # insert a box at same index.
                    break

        wh.worker = attemptCoor        # move a worker
        return self.warehouse_to_state(wh)
    
    def path_cost(self, c, state1, action, state2):
        """Return the cost of a solution path that arrives at state2 from
        state1 via action, assuming cost c to get up to state1. If the problem
        is such that the path doesn't matter, this function will only look at
        state2.  If the path does matter, it will consider c and maybe state1
        and action. The default method costs 1 for every step in the path.

        Since path matters in this problem , we will override this function.
        move_cost of a worker is always 1 in this problem.

        Returns:
            prevcost + move_cost + box_weight

        """

        wh = self.state_to_warehouse(state1)

        deltaDir = direction(action)
        attemptCoor = move_towards(wh.worker,deltaDir)
        move_cost = 1 # the worker move cost is always 1
        box_weight = 0 
        if(is_coordinate_box(wh,attemptCoor)): # if it bumps into a box            
                # move a box
                for i,boxCor in enumerate(wh.boxes):
                    if ( boxCor == attemptCoor ):
                        box_weight = self.warehouse.weights[i]
                        break

        return c + move_cost + box_weight


    

    def get_seq_from_goalnode(self, goal_node):
        """
            Shows solution represented by a specific goal node.
          
            Returns:
                List of actions to reach the goal.
        """
        path = goal_node.path()
        return [seq.action for seq in path if seq.action]
      
    def h(self, node):
        '''
            Returns (Admissible,Consistent) Heurstics value of current node (estimated cost) to goal.

            move_cost of a worker is always 1 in this problem.

            h_box  = For each box, find mahattan distance of the nearest target * (  weight + move_cost)
            h_worker = min [mahattan distance of worker and boxes].
            move_cost is subtracted since finding the distance of worker to a box which can be pushed.
            
            Ye Gaung Comments:

                Calculating distances, we wil assume there are no obstacles between elements.
                For h_box, it means more than one box can go into the same target cell.

                Because of above statements,t his kind of heurstics is optimistic since it always understimates to reach to the goal.

            Returns : 
                 h = h_box + h_worker - move_cost

                
        '''
        if(isinstance(node,search.Node)):
            h_box = 0
            h_worker = 0
            move_cost = 1 # the worker move cost is always 1
            min_worker_distance = None
            for i,boxCor in enumerate(node.state[1]):
                worker_distance = find_manhattan(boxCor,node.state[0])
                if min_worker_distance == None or worker_distance < min_worker_distance:
                    min_worker_distance = worker_distance
                min_box_distance = None                
                for targetCor in self.warehouse.targets:
                    box_distance = find_manhattan(boxCor,targetCor) * (self.warehouse.weights[i] + move_cost)
                    if min_box_distance == None or box_distance < min_box_distance:
                        min_box_distance = box_distance
                h_box+= min_box_distance # h_box is now sum of distances and weights  of a box to nearest target.
            h_worker = min_worker_distance

            return h_worker + h_box -move_cost
            # return 0

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def check_elem_action_seq(warehouse, action_seq):
    '''
    
    Determine if the sequence of actions listed in 'action_seq' is legal or not.
    
    Important notes:
      - a legal sequence of actions does not necessarily solve the puzzle.
      - an action is legal even if it pushes a box onto a taboo cell.
        
    @param warehouse: a valid Warehouse object

    @param action_seq: a sequence of legal actions.
           For example, ['Left', 'Down', Down','Right', 'Up', 'Down']
           
    @return
        The string 'Impossible', if one of the action was not valid.
           For example, if the agent tries to push two boxes at the same time,
                        or push a box into a wall.
        Otherwise, if all actions were successful, return                 
               A string representing the state of the puzzle after applying
               the sequence of actions.  This must be the same string as the
               string returned by the method  Warehouse.__str__()
    

    Ye Gaung Comments:

        illegal action
            1. Player Trying to move into a wall.
            2. Player Trying to push a box into a wall.
            3. Player Trying to push more than one boxes.

    '''

    for seq in action_seq:
        
        deltaDir = direction(seq)
        attemptCoor = move_towards(warehouse.worker,deltaDir)

        if(is_coordinate_wall(warehouse,attemptCoor)): # if it bumps into a wall.
            return "Impossible"
        elif(is_coordinate_box(warehouse,attemptCoor)): # if it bumps into a box. Need to check more.
            if(is_coordinate_wall(warehouse,move_towards(attemptCoor,deltaDir))):  # if a tile ahead is a wall.
                return "Impossible"
            elif(is_coordinate_box(warehouse,move_towards(attemptCoor,deltaDir))): # if a tile ahead is another box.
                return "Impossible"
            else:
                # move a box
                for i,boxCor in enumerate(warehouse.boxes):
                    if(boxCor == attemptCoor ):
                        warehouse.boxes.pop(i) # remove that box 
                        warehouse.boxes.insert(i,move_towards(attemptCoor,deltaDir)) # insert a box at same index.
                        break
        
        #move a worker
        warehouse.worker = attemptCoor

    return(str(warehouse))
     
   

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def solve_weighted_sokoban(warehouse):
    '''
    This function analyses the given warehouse.
    It returns the two items. The first item is an action sequence solution. 
    The second item is the total cost of this action sequence.
    
    @param 
     warehouse: a valid Warehouse object

    @return
    
        If puzzle cannot be solved 
            return 'Impossible', None
        
        If a solution was found, 
            return S, C 
            where S is a list of actions that solves
            the given puzzle coded with 'Left', 'Right', 'Up', 'Down'
            For example, ['Left', 'Down', Down','Right', 'Up', 'Down']
            If the puzzle is already in a goal state, simply return []
            C is the total cost of the action sequence C

    '''   

    taboocells = find_taboo_cells(warehouse)

    for box in warehouse.boxes: 
        for taboo in taboocells:     # check boxes are in taboo cells, 
            if(box == taboo):
                return "Impossbile",None     # return 'Impossible', None

    sp = SokobanPuzzle(warehouse,taboocells)
    
    sol_gs = search.astar_graph_search(sp)

    if(sol_gs == None):# no Soultion
        return "Impossible", None
    else:
        seq = sp.get_seq_from_goalnode(sol_gs)
        return seq,sol_gs.path_cost


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def direction (dirInText : str) -> tuple:
    '''
    Convert direction into a vector.

    - "Left"  -> (-1, 0)
    - "Right" -> ( 1, 0)
    - "Up"    -> ( 0,-1)
    - "Down"  -> ( 0, 1)

    Params:
        - dirInText : str (any string other than above four will raise errors)

    Returns:
        - direction vector in tuple .
    '''

    dir = None
    if(dirInText == "Left"):
        dir = (-1,0)
    elif(dirInText == "Right"):
        dir = (1,0)
    elif(dirInText == "Up"):
        dir = (0,-1)
    elif(dirInText == "Down"):
        dir = (0,1)    
    assert dir != None
    return dir

def is_coordinate_wall(warehouse : Warehouse,coordinate : tuple) -> bool:

    '''
    Check if a given Coordinate is a wall in a given Warehouse.

    Params:
        - warehouse : warehouse to check
        - coordinate: coordinate in tuple to check

    Returns:
        - True if coordiante has a wall, else False
    '''

    if(len(coordinate) != 2):
        raise ValueError("Coordinate Should Have two values.")
    if(coordinate in warehouse.walls):
        return True
    return False

def is_coordinate_box(warehouse : Warehouse,coordinate : tuple) -> bool:

    '''
    Check if a given Coordinate has a box in a given Warehouse.

    Params:
        - warehouse : warehouse to check
        - coordinate: coordinate in tuple to check

    Returns:
        - True if coordiante has a box, else False
    '''

    if(len(coordinate) != 2):
        raise ValueError("Coordinate Should Have two values.")
    if(coordinate in warehouse.boxes):
        return True
    return False


def find_corner_cells(warehouse: Warehouse) -> list: 
    '''
    Find all invalid corners of a warehouse.

    A corner will not be counted if it is a target cell.

    Params:
        - warehouse : warehouse to check

    Returns:
        - Coordinates of corner cells in List

    '''
    corners = []
    for y in range(warehouse.nrows):
        for x in range(warehouse.ncols):
            if( not (x,y) in warehouse.walls and not (x,y) in warehouse.targets):
                if( ((x-1,y) in warehouse.walls and (x,y-1) in warehouse.walls) or 
                    ((x-1,y) in warehouse.walls and (x,y+1) in warehouse.walls) or
                    ((x+1,y) in warehouse.walls and (x,y-1) in warehouse.walls) or
                    ((x+1,y) in warehouse.walls and (x,y+1) in warehouse.walls)
                ):
                    corners.append((x,y))
    return corners 

def find_taboo_cells(warehouse: Warehouse) -> list:
    '''
    Find all invalid taboo cells of a warehouse.

    This is not optimized well and will not cover all possible taboo cells.
    Since it is going to execute only once at start
    Nevertheless, it can eliminate many unsolvable nodes. 

    Params:
        - warehouse : warehouse to check

    Returns:
        - Coordinates of taboo cells in List

    '''
    corners = find_corner_cells(warehouse)
    taboos = []
    for x,y in corners:
        for (dx,dy) in [(1,0),(-1,0),(0,1),(0,-1)]:
            checking_cell = (x + dx,y + dy)
            if dy == 0: # for horizontal axis check                
                if( checking_cell in corners or checking_cell in warehouse.walls or checking_cell in warehouse.targets):
                    continue
                checking_cell = move_towards(checking_cell, (dx,dy))

                while(not checking_cell in corners  ):
                    if(checking_cell in warehouse.targets or checking_cell in warehouse.walls or checking_cell[0] < 0  or checking_cell[0] > warehouse.ncols - 1):
                        break
                    checking_cell = move_towards(checking_cell, (dx,dy))

                if(checking_cell in warehouse.targets or checking_cell in warehouse.walls or checking_cell[0] < 0  or checking_cell[0] > warehouse.ncols - 1):
                    continue

                t = []
                is_set_taboo = True
                checking_cell = move_towards(checking_cell, (-dx,-dy))

                while(checking_cell != (x,y) ):                                                                                            
                    t.append((checking_cell))
                    checking_cell = move_towards(checking_cell, (-dx,-dy))

                for potential_taboo in t :
                    # bayy nar ka kaung ka taboo or corner or walls ma phit yin
                    if not ((potential_taboo[0], potential_taboo[1]-1) in warehouse.walls) :
                        is_set_taboo = False
                        break

                if(not is_set_taboo):
                    is_set_taboo = True
                    for potential_taboo in t :
                        if not ((potential_taboo[0], potential_taboo[1]+1) in warehouse.walls) :
                            is_set_taboo = False
                            break

                if(not is_set_taboo):
                    t = []
                
                taboos = taboos + t  

            if dx == 0: # for vertical axis check                
                if( checking_cell in corners or checking_cell in warehouse.walls or checking_cell in warehouse.targets):
                    continue
                checking_cell = move_towards(checking_cell, (dx,dy))

                while(not checking_cell in corners  ):
                    if(checking_cell in warehouse.targets or checking_cell in warehouse.walls or checking_cell[1] < 0  or checking_cell[1] > warehouse.nrows - 1):
                        break
                    checking_cell = move_towards(checking_cell, (dx,dy))

                if(checking_cell in warehouse.targets or checking_cell in warehouse.walls or checking_cell[1] < 0  or checking_cell[1] > warehouse.nrows - 1):
                    continue

                t = []
                is_set_taboo = True
                checking_cell = move_towards(checking_cell, (-dx,-dy))

                while(checking_cell != (x,y) ):                                                                                            
                    t.append((checking_cell))
                    checking_cell = move_towards(checking_cell, (-dx,-dy))

                for potential_taboo in t :
                    # bayy nar ka kaung ka taboo or corner or walls ma phit yin
                    if not ((potential_taboo[0]-1, potential_taboo[1]) in warehouse.walls) :
                        is_set_taboo = False
                        break

                if(not is_set_taboo):
                    is_set_taboo = True
                    for potential_taboo in t :
                        if not ((potential_taboo[0]+1, potential_taboo[1]) in warehouse.walls) :
                            is_set_taboo = False
                            break

                if(not is_set_taboo):
                    t = []
                
                taboos = taboos + t  

    return list(set(corners + taboos))

def find_manhattan(p1, p2):
    '''
        Find mahattan distance between p1 and p2 ( corresonpondingly until elements from one point run out)
        
        Params:
            p1 : first point
            p2 : second point

        Returns:
            mahattan distance between two points.
    '''
    return sum(abs(sum1-sum2) for sum1, sum2 in zip(p1,p2))

def move_towards(point : tuple , deltaDir : tuple) -> tuple:
    '''
    Calculate the result coordinate of "point + deltaDir"

    Params:
        - point : Starting Point
        - deltaDir : Direction to move

    Returns;
        gives point+deltaDir in tuple
    '''
    if(len(point) != 2  or len(deltaDir) !=2 ):   
        raise ValueError("Coordinate Should Have two values.")
    return (point[0] + deltaDir[0], point[1] + deltaDir[1])