'''

This module defines utility functions and classes for a Sokoban assignment.

The main class is the Warehouse class.

An instance of this class can read a text file coding a Sokoban puzzle,
and  store information about the positions of the walls, boxes and targets 
list. See the header comment of the Warehouse class for details


Last modified by 2022-03-27  by f.maire@qut.edu.au
- added weights to the boxes

'''

import operator
import functools


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#                           UTILS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def find_1D_iterator(line, char):
    '''
    Return a generator that yield the positions (offset indices)
       where the character 'char' appears in the  'line' string.
    line : a string where we might find occurences of the 'char' character.
    char : a character that we are looking for.
    '''
    pos = 0
    # To see the doc of the string method 'find',  type  help(''.find)
    pos = line.find(char, pos)
    while pos != -1:
        yield pos
        pos = line.find(char, pos+1)


def find_2D_iterator(lines, char):
    '''
    Return a generator that  yields the (x,y) positions of
       the occurences of the character 'char' in the list of string 'lines'.
       A tuple (x,y) is returned, where
          x is the horizontal coord (column offset),
          and  y is the vertical coord (row offset)
    lines : a list of strings.
    char : the character we are looking for.
    '''
    for y, line in enumerate(lines):
        for x in find_1D_iterator(line, char):
            yield (x,y)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class Warehouse:
    '''
    A Warehouse instance represents the initial configuration of a warehouse
    in a Sokoban puzzle. The information stored in a Warehouse instance 
    includes the position of the walls, targets, boxes and the worker.
    The attributes 'self.boxes', 'self.targets' and 'self.walls'
    are tuples of (x,y) coordinates (x <-> columns, y <-> rows).
    The attribute 'self.worker' is a tuple (x,y)
    The origin is at the top left. 
    The horizontal axis 'x' is pointing right.
    The vertical axis 'y' is pointing down.  
    The attributes  self.nrows and self.ncols are 
    the number of rows and cols of the warehouse.
    
    The attribute self.weights contains the weights of the boxes.
    If self.weights != None then self.weights[i] is the weight of the
    ith box. 
    
    The weights of the boxes are used in the computation of the cost
    of the pushing actions.
    
    '''
    def copy(self, worker = None, boxes = None, weights = None):
        '''
        Return a clone of this warehouse. 
        Possibly with new positions for the worker and the boxes 
        if the values of these parameters are not 'None'.
        All parameters should be None or tuples
        @param
            worker : a (x,y) tuple, position of the agent
            boxes : sequence of (x,y) pairs, positions of the boxes
            weights : sequence of weights of the boxes (same order as 'boxes')
        '''
        clone = Warehouse()
        clone.worker = worker or self.worker
        clone.boxes = boxes or self.boxes
        clone.weights = weights or self.weights
        clone.targets = self.targets
        clone.walls = self.walls
        clone.ncols = self.ncols
        clone.nrows = self.nrows
        return clone

    def from_string(self, warehouse_str):
        '''
        Create a warehouse from a string.
        '''
        lines = warehouse_str.split(sep='\n')
        self.from_lines(lines)

    def load_warehouse(self, filePath):
        '''
        Load a warehouse stored in a text file.
        '''
        with open(filePath, 'r') as f:
            # 'lines' is a list of strings (rows of the puzzle) 
            lines = f.readlines() 
        self.from_lines(lines)
        # self.weights = None # all boxes are of weight 1
            
    def from_lines(self, lines):
        '''
        Create a warehouse from a list of lines,
        where each line is the string representation of a row 
        of a warehouse.
        '''
        # Put the warehouse in a canonical format
        # where row 0 and column 0 have both at least one brick.
        first_row_brick, first_column_brick = None, None
        for row, line in enumerate(lines):
            brick_column = line.find('#')
            if brick_column>=0: 
                if  first_row_brick is None:
                    first_row_brick = row # found first row with a brick
                if first_column_brick is None:
                    first_column_brick = brick_column
                else:
                    first_column_brick = min(first_column_brick, brick_column)
        if first_row_brick is None:
            raise ValueError('Warehouse with no walls!')
        # compute the canonical representation
        # keep only the lines that contain walls
        canonical_lines = [line[first_column_brick:] 
                           for line in lines[first_row_brick:] if line.find('#')>=0]
        
        self.ncols = 1+max(line.rfind('#') for line in canonical_lines)
        self.nrows = len(canonical_lines)
        self.extract_locations(canonical_lines)
        
        # Weights if provided are on the first line   
        try:
            W = [int(v) for v in lines[0].split()]
        except:
            W = None
        # W can be an empty list if first line is blank
        if W is not None and len(W)>0:
            assert len(W) == len(self.boxes)
            self.weights = W
        else:
            self.weights = [0] * len(self.boxes)   
        #debug
        # print(f'{self.weights}')
    
    def save_warehouse(self, filePath):
        '''
        Save the string representation of the warehouse
        in a text file. The text file can be loaded later with
        'load_warehouse'
        '''
        with open(filePath, 'w') as f:
            f.write(self.__str__())

    def extract_locations(self, lines):
        '''
        Extract positional information from the the list of string 'lines'.
        The list of string 'lines' represents the puzzle.
        This function sets the fields
          self.worker, self.boxes, self.targets and self.walls
        '''
        workers =  list(find_2D_iterator(lines, "@"))  # workers on a free cell
        workers_on_a_target = list(find_2D_iterator(lines, "!"))
        # Check that we have exactly one agent
        assert len(workers)+len(workers_on_a_target) == 1 
        if len(workers) == 1:
            self.worker = workers[0]
        self.boxes = list(find_2D_iterator(lines, "$")) # crate/box
        self.targets = list(find_2D_iterator(lines, ".")) # empty target
        targets_with_boxes = list(find_2D_iterator(lines, "*")) # box on target
        self.boxes += targets_with_boxes
        # organize the boxes in reading order
        self.boxes.sort(key=lambda p:(p[1],p[0]))
        self.targets += targets_with_boxes
        if len(workers_on_a_target) == 1:
            self.worker = workers_on_a_target[0]
            self.targets.append(self.worker) 
        self.walls = list(find_2D_iterator(lines, "#")) # set(find_2D_iterator(lines, "#"))
        assert len(self.boxes) == len(self.targets)

    def __str__(self):
        '''
        Return a string representation of the warehouse
        '''
        ##        x_size = 1+max(x for x,y in self.walls)
        ##        y_size = 1+max(y for x,y in self.walls)
        X,Y = zip(*self.walls) # pythonic version of the above
        x_size, y_size = 1+max(X), 1+max(Y)
        
        vis = [[" "] * x_size for y in range(y_size)]
        # can't use  vis = [" " * x_size for y ...]
        # because we want to change the characters later
        for (x,y) in self.walls:
            vis[y][x] = "#"
        for (x,y) in self.targets:
            vis[y][x] = "."
        # if worker is on a target display a "!", otherwise a "@"
        # exploit the fact that Targets has been already processed
        if vis[self.worker[1]][self.worker[0]] == ".": # Note y is worker[1], x is worker[0]
            vis[self.worker[1]][self.worker[0]] = "!"
        else:
            vis[self.worker[1]][self.worker[0]] = "@"
        # if a box is on a target display a "*"
        # exploit the fact that Targets has been already processed
        for (x,y) in self.boxes:
            if vis[y][x] == ".": # if on target
                vis[y][x] = "*"
            else:
                vis[y][x] = "$"
        return "\n".join(["".join(line) for line in vis])

    # def __eq__(self, other):
    #     return self.worker == other.worker and \
    #            self.boxes == other.boxes

    def __hash__(self):
        return hash(self.worker) ^ functools.reduce(operator.xor, [hash(box) for box in self.boxes])
    
if __name__ == "__main__":
    wh = Warehouse()
    wh.load_warehouse("./warehouses/ygkTest.txt")

    print(wh)   # this calls    wh.__str__()


# + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + 
#                              CODE CEMETARY
# + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + +


