#!/usr/bin/env python

import tkinter as tk
from tkinter.filedialog import askopenfilename
    
import os

from sokoban import Warehouse

# Written by f.maire@qut.edu.au using icon images from Risto Stevcev.
# Last modified on 2022/05/2
# fix the inconsistency of the capitalization of 'impossible'

import time

__author__ = "Frederic Maire"
__version__ = "2.0"


try:
    from fredSokobanSolver import solve_weighted_sokoban
    print("Using Fred's solver")
except ModuleNotFoundError:
    from mySokobanSolver import solve_weighted_sokoban
    print("Using submitted solver")

    

# directory where this file is located
app_root_folder = os.getcwd()

# creating tkinter root/main window
root_window = tk.Tk()
root_window.geometry('550x180')

# tk.Frame containing the warehouse
frame = tk.Frame(master=root_window)
frame.pack()

# move actions 
direction_offset = {'Left' :(-1,0), 'Right':(1,0) , 'Up':(0,-1), 'Down':(0,1)} # (x,y) = (column,row)

# dictionary of images for the display of the warehouse
image_dict={'wall':tk.PhotoImage(file=os.path.join(app_root_folder, 'images/wall.gif')),
                 'target':tk.PhotoImage(file=os.path.join(app_root_folder, 'images/hole.gif')),
                 'box_on_target':tk.PhotoImage(file=os.path.join(app_root_folder, 'images/crate-in-hole.gif')),
                 'box':tk.PhotoImage(file=os.path.join(app_root_folder, 'images/crate.gif')),
                 'worker':tk.PhotoImage(file=os.path.join(app_root_folder, 'images/player.gif')),
                 'smiley':tk.PhotoImage(file=os.path.join(app_root_folder, 'images/smiley.gif')),
                 'worker_on_target':tk.PhotoImage(file=os.path.join(app_root_folder, 'images/player-in-hole.gif')),
                 }



#----------------------------------------------------------------------------

#  Global variables

# file path to the current warehouse
warehouse_path = None
warehouse = None
cells = dict()  # cells[(x,y)] is the canvas of the cell (x,y) of the warehouse
solution = None # sequence of action returned by the solver (or 'Impossible')

#----------------------------------------------------------------------------

def welcome_frame():
     tk.Label(frame, text="\n *** Welcome to Sokoban! ***\n").grid(row=0, column=0)

     tk.Label(frame, text="To load a warehouse: File -> Open\n").grid(row=1, column=0)

     tk.Label(frame, text="To reset the current warehouse: press the 'r' key \n").grid(row=3, column=0)

     tk.Label(frame, text="To call your solve_weighted_sokoban solver: Solve -> Plan action sequence\n").grid(row=4, column=0)

     tk.Label(frame, text="To step through your solution: press the 's' key \n").grid(row=5, column=0)

     tk.Label(frame, text="To print help on the console: press the 'h' key \n").grid(row=6, column=0)

     frame.pack()
     
#----------------------------------------------------------------------------

def get_box_weight(x,y):
    '''
    Get the weight of the box at position x,y
    in the current warehouse.
    If no weight given return 0
    '''
    try:
        w = warehouse.weights[warehouse.boxes.index((x,y))]
    except:
        w = 0
    return w

#----------------------------------------------------------------------------

def make_cell(cell_type, box_weight = None):
    '''
    Create a canvas for a cell of the warehouse
    Return a painted canvas
    
    PRE: 
        frame has been created
    '''
    canvas = tk.Canvas(frame,
                       width=50, 
                       height=50)
    background_image = image_dict[cell_type]
    canvas.create_image(0, 0, anchor=tk.NW, image=background_image)
    if box_weight != None:
        canvas.create_text(25, 25, text= str(box_weight),
                       fill="black",font=('Helvetica 15 bold'))
    return canvas

#----------------------------------------------------------------------------

def clear_level():
    '''
    Clear the current warehouse (aka level)    
    '''
    global frame, warehouse, cells, solution
    if frame:
        frame.destroy()
    frame = tk.Frame(master=root_window)
    warehouse = Warehouse() # warehouse
    cells = dict() 
    solution = None

# ----------------------------------------------------------------------------

def select_warehouse():
    '''
    Load a warehouse
    '''
    global frame, warehouse_path
    # frame.pack_forget() # todo: move this line to clear_level?!
    warehouse_path = askopenfilename(
                        initialdir=os.path.join(app_root_folder, 'warehouses'))
    print( f"Loading warehouse {warehouse_path}")
    start_level()
    
# ----------------------------------------------------------------------------

def start_level():
    '''
    Reset the warehouse and display it    
    '''
    clear_level()
    warehouse.load_warehouse(warehouse_path)
    root_window.title(f'Sokoban v{__version__} - {warehouse_path.split("/")[-1]}' )
    geom = str(warehouse.ncols*52)+'x'+str(warehouse.nrows*52)
    root_window.geometry(geom)
    fresh_display()
 
# ----------------------------------------------------------------------------

def clean_cell(x,y):
    '''
    Destroy the widget in cells[(x,y)] and remove the entry 
    from the dictionary
    '''
    if (x,y) in cells:
        cells[(x,y)].destroy()
        del cells[(x,y)]
    
# ----------------------------------------------------------------------------

def fresh_display():
    '''
    First display of the warehouse
    Setup the cells dictionary
    '''
    for x,y in warehouse.walls:
        cells[(x,y)] = make_cell('wall')
        cells[(x,y)].grid(row=y,column=x)
    for x,y in warehouse.targets:
        cells[(x,y)] = make_cell('target')
        cells[(x,y)].grid(row=y,column=x)
    for x,y in warehouse.boxes:
        if (x,y) in warehouse.targets:
            clean_cell(x,y)
            cells[(x,y)] = make_cell('box_on_target', get_box_weight(x, y))      
            cells[(x,y)].grid(row=y,column=x)
        else:
            cells[(x,y)] = make_cell('box', get_box_weight(x,y))      
            cells[(x,y)].grid(row=y,column=x)
    x,y = warehouse.worker
    if (x,y) in warehouse.targets:
        cells[(x,y)].destroy() 
        cells[(x,y)] = make_cell('worker_on_target')      
    else:
        cells[(x,y)] = make_cell('worker')      
    cells[(x,y)].grid(row=y,column=x)
    frame.pack(fill = tk.BOTH, expand = True)
    
# ----------------------------------------------------------------------------

def move_player(direction):
    '''
    direction in ['Left', 'Right', 'Up', 'Down']:
    Check whether the worker is pushing a box
    '''
    global warehouse
    x,y = warehouse.worker
    xy_offset = direction_offset[direction]
    next_x , next_y = x+xy_offset[0] , y+xy_offset[1] # where the player will go if possible
    # Let's find out if it is possible to move the player in this direction
    if (next_x,next_y) in warehouse.walls:
        return # impossible move, do nothing
    if (next_x,next_y) in warehouse.boxes:
        if try_move_box( (next_x,next_y), (next_x+xy_offset[0],next_y+xy_offset[1]) ) == False:
            return # box next to the player could not be pushed
    # now, the cell next to the player must be empty or with a box that can be moved
    # we still have to move the player
    clean_cell(x, y)
    clean_cell(next_x,next_y)
    # Test whether the appearance of the player need to change on the next cell
    if (next_x,next_y) in warehouse.targets:
        cells[(next_x,next_y)] = make_cell('worker_on_target')
    else:
        cells[(next_x,next_y)] = make_cell('worker')
    cells[(next_x,next_y)].grid(row=next_y,column=next_x) # move it to the next cell
    warehouse.worker = (next_x,next_y)
    # update the cell where the player was
    if (x,y) in warehouse.targets:
        # cell x,y has already been cleaned
        cells[(x,y)] = make_cell('target')      
        cells[(x,y)].grid(row=y,column=x)
    puzzle_solved = all(z in warehouse.targets for z in warehouse.boxes)
    if puzzle_solved:
        x,y = warehouse.worker
        # widget in the cell currently containing the player
        clean_cell(x, y)
        cells[(x,y)] = make_cell('smiley') 
        cells[(x,y)].grid(row=y,column=x)
    frame.pack()
          
# ----------------------------------------------------------------------------

def try_move_box(location, next_location):
    '''
    location and next_location are (x,y) tuples
    Move the box  from 'location' to 'next_location'
    Note that we assume that there is a wall around the warehouse!
    Return True if the box was moved, return False if the box could not be moved
    Update the position and the image of the  widget for this box
    '''
    x, y = location
    next_x, next_y = next_location

    assert (x,y) in warehouse.boxes
    if (next_x, next_y) not in warehouse.walls and (next_x, next_y) not in warehouse.boxes:
        # can move the box!
        # the cell (x,y) is cleaned by 'move_player'
        # clean cell (next_x,next_y)
        if (next_x,next_y) in cells:
            assert (next_x,next_y) in warehouse.targets
            clean_cell(next_x,next_y)
        # new widget for the moved box
        if (next_x,next_y) in warehouse.targets:
            cells[(next_x,next_y)] = make_cell('box_on_target', get_box_weight(x,y))            
        else:
            cells[(next_x,next_y)] = make_cell('box',  get_box_weight(x,y)) 
        cells[(next_x,next_y)].grid(row=next_y, column=next_x)
        # we have to preserve the position of the box in the list boxes
        bi = warehouse.boxes.index((x,y))
        warehouse.boxes[bi] = (next_x,next_y)
        # we don't have to update (x,y), this will be done while moving the player
        return True # move successful
    else:
        return False # box was blocked

# ----------------------------------------------------------------------------

def solve_puzzle():
    global solution
    if warehouse is None:
        print('\nFirst load a warehouse!!\n')
        return
    print('\nStarting to think...\n')
    t0 = time.time()
    solution, total_cost = solve_weighted_sokoban(warehouse)
    t1 = time.time()
    print (f'\nAnalysis took {t1-t0:.6f} seconds\n')
    if solution == 'Impossible':
        print('\nNo solution found!\n')
    else:
        print(f"\nSolution found with a cost of {total_cost} \n", solution, '\n')
    
# ----------------------------------------------------------------------------
    
def play_solution():
    global solution
    if solution and len(solution) > 0:
        move_player(solution.pop(0))
        root_window.after(300, play_solution)
    
# ----------------------------------------------------------------------------

def key_handler(event):
    if event.keysym in ('Left', 'Right', 'Up', 'Down'): 
        move_player(event.keysym)
    if event.keysym in ('r','R'):
        if warehouse_path:
            start_level()
    if event.keysym in ('s','S'):
        if solution and len(solution) > 0:
            move_player(solution.pop(0))
    if event.keysym in ('h','H'):
        print(
'''
To load a warehouse: File -> Open
To reset the current warehouse: press the 'r' key
To call your solve_weighted_sokoban solver: Plan action sequence 
To step through your solution: press the 's' key 
To print help on the console: press the 'h' key 
''')

# ----------------------------------------------------------------------------
        
#  Create the GUI        
        
root_window.title('Weighted Sokoban')
root_window.iconphoto(
    False, 
    tk.PhotoImage(file=os.path.join(app_root_folder, 'images/crate.gif'))
    )


# Creating Menubar
menubar = tk.Menu(root_window)
root_window.config(menu=menubar)
  
# Adding File Menu and commands
file_menu = tk.Menu(menubar, tearoff = 0)
menubar.add_cascade(label ='File', menu = file_menu)
file_menu.add_command(label ='Load warehouse', command = select_warehouse)
file_menu.add_command(label="Restart puzzle", command=start_level)
file_menu.add_separator()
file_menu.add_command(label ='Quit', command = root_window.destroy)

# Adding File Solve Menu and commands
solve_menu = tk.Menu(menubar, tearoff = 0)
menubar.add_cascade(label ='Solve', menu = solve_menu)
solve_menu.add_command(label ='Plan action sequence', command = solve_puzzle)
solve_menu.add_command(label ='Play action sequence', command = play_solution)


clear_level()
welcome_frame()

root_window.bind_all("<Key>", key_handler)
root_window.mainloop()

# + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + 
#                              CODE CEMETARY
# + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + 


