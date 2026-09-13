import pymycobot
from pymycobot.mycobot import MyCobot

def center(mc, speed):
    mc.send_angles([0,0,0,0,0,0],speed)

def process_gcode(file_path, get_coords):

    """
    Parse the contents of the gcode file, extract the XYZ coordinate values, and save the coordinate data into a list
    :param file_path: Gcode file path
    :return: A coordinate list
    """
    # The last valid coordinate, using the rx, ry, rz values
    # in the current coordinates of the robot arm as the starting attitude
    data_coords = []
    
    last_coords = [0.0, 0.0, 0.0, get_coords[3], get_coords[4], get_coords[5]]
    with open(file_path, 'r') as file:
        # Line-by-line processing instructions
        for line in file:
            command = line.strip()  # Remove newline characters and other whitespace characters at the end of the line
            if command.startswith("G0") or command.startswith("G1"):  # Move command
                coords = last_coords[:]  # Copy the previous valid coordinates
                command_parts = command.split()
                for part in command_parts[1:]:
                    if part.startswith("X") or part.startswith("x"):
                        coords[0] = float(part[1:])  # Extract and transform X coordinate data
                    elif part.startswith("Y") or part.startswith("y"):
                        coords[1] = float(part[1:])  # Extract and transform Y coordinate data
                    elif part.startswith("Z") or part.startswith("z"):
                        coords[2] = float(part[1:])  # Extract and transform Z coordinate data
                if coords[0] == 0.0 and coords[1] == 0.0:  # If XY data is missing, use the last valid XY coordinates
                    coords[0] = last_coords[0]
                    coords[1] = last_coords[1]
                if coords[2] == 0.0:  # If Z data is missing, use the last valid Z coordinate
                    coords[2] = last_coords[2]
                last_coords = coords
                data_coords.append(coords)  # Add coordinates to list and save
    return data_coords