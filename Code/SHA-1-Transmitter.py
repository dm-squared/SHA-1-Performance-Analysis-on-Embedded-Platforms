####################################################################################
###                                                                              ###
###               ECE 4300 - Computer Architecture Spring 2022                   ###
###   Term Project: SHA-1 Algorithm Performance on Multiple Embedded Platforms   ###
###                                                                              ### 
###                             Transmitter Side                                 ###
###                                                                              ###
###            By: Derek Mata, Christopher Yamada, Elizabeth Hwang               ###
###                                                                              ###
####################################################################################

# How to hash with SHA-1: https://stackoverflow.com/questions/22058048/hashing-a-file-in-python

# General python libraries
import sys

# Metric calculating libraries
import platform
import os
import datetime
import psutil
from resource import *

# Hashing library
import hashlib

# Network connection library
import socket



# List to hold all strings to enter into txt file at end
text_to_push_list_results = list()
text_to_push_list_hashes = list()

# Path for results.txt file
HOME_DIR = os.path.dirname(__file__)
results_txt_file_path = os.path.abspath( os.path.join(HOME_DIR, "SHA-1-results-tx.txt") )

# Path for the .txt file we will be hashing
original_txt_file_path = os.path.abspath( os.path.join(HOME_DIR, "original.txt") )

# Path for the .txt file we will be sending over the network
send_txt_file_path = os.path.abspath( os.path.join(HOME_DIR, "send.txt") )

# Path for storing all hashed values into 
hash_txt_file_path = os.path.abspath( os.path.join(HOME_DIR, "hashes.txt") )



#################################
#                               #
#      HARDWARE INFORMATION     #
#                               #
#################################
def get_hw_info() -> None:
    machine_type = platform.machine()
    processor_type = platform.processor()
    number_phy_cores = psutil.cpu_count(logical=False)
    number_logic_cores = psutil.cpu_count(logical=True)
    RAM_installed = round( psutil.virtual_memory().total / 1000000000, 2 )
    Max_CPU_freq = psutil.cpu_freq().max
    return [machine_type, processor_type, number_phy_cores, number_logic_cores, RAM_installed, Max_CPU_freq]


#################################
#                               #
#      SOFTWARE INFORMATION     #
#                               #
#################################
def get_sw_info() -> None:
    operating_system = platform.platform()
    py_interpreter = platform.python_compiler()
    py_version = platform.python_version()
    return [operating_system, py_interpreter, py_version]


#################################
#                               #
#          FILE WRITING         #
#                               #
#################################
# Create the header file for result.txt file
def make_results_txt_header(hw_name: str) -> None:
    global text_to_push_list_results
    text_to_push_list_results.append("----- RESULTS FROM THE " + hw_name.upper() + " SHA-1 RECEIVER SCRIPT -----\r")
    
############################

# Push text to list which will later be written to file
def push_text(line: str, type="results") -> None:
    global text_to_push_list_results
    global text_to_push_list_hashes
    if(type == "results"):
        text_to_push_list_results.append(line)
        print(line)
    elif(type == "hashes"):
        text_to_push_list_hashes.append(line)
    
############################

# Create the text file we will store results in
def create_txt_file(type="results") -> None:
    global results_txt_file_path
    global hash_txt_file_path
    os.umask(0)
    if(type == "results"):
        file = os.open(results_txt_file_path, os.O_CREAT, 0o777)
    elif(type == "hashes"):
        file = os.open(hash_txt_file_path, os.O_CREAT, 0o777)
    elif(type == "send"):
        file = os.open(send_txt_file_path, os.O_CREAT, 0o777)
    else:
        raise Exception("create_txt_file: type only accepts input of \'hashes\', \'send\', or \'results\'")
    os.close(file)
    
############################

# Write to text file we store results in
def write_txt_file(type="results", buffer=[None]) -> None:
    global results_txt_file_path
    global text_to_push_list_results
    global hash_txt_file_path
    global text_to_push_list_hashes
    
    if(type == "results"):
        file = open(results_txt_file_path, "a")
        for line in text_to_push_list_results:
            file.write(line)
            file.write("\r")
        file.close()
    elif(type == "hashes"):
        file = open(hash_txt_file_path, "a")
        for line in text_to_push_list_hashes:
            file.write(line)
            file.write("\r")
        file.close()
    elif(type == "send"):
        file = open(send_txt_file_path, "a")
        for line in buffer:
            file.write(line)
            file.write("\r")
        file.close()
    else:
        raise Exception("write_txt_file: type only accepts input of \'hashes\', \'send\', or \'results\'")


#################################
#                               #
#     NETWORK FILE TRANSFER     #
#                               #
#################################
# Create the client socket and transfer data using utf-8 encoding
def transfer_data_to_receiver():
    client_ip = socket.gethostbyname(socket.gethostname())
    client_port = 64321
    RECV_BUFFER = 1024 
    
    # Open TCP socket to connect to receiver
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # Connect to TCP welcome port of server
        client_socket.connect((client_ip, client_port))
        
        # Try and send hashes.txt file to server, then receive server ACK
        with open(hash_txt_file_path, "rb") as file:
            client_socket.sendfile(file, 0)
            file.close()
        server_ack = client_socket.recv(RECV_BUFFER)
        print(str(server_ack))
    
        # Try and send original.txt file to server, then receive server ACK
        with open(send_txt_file_path, "rb") as file:
            client_socket.sendfile(file, 0)
            file.close()
        server_ack = client_socket.recv(RECV_BUFFER)
        print(str(server_ack))
        
        # Close the connection
        client_socket.close()



#################################
#                               #
#         MAIN FUNCTION         #
#                               #
#################################
def main():
    # Get name of embedded device user is running on
    print("Please enter which platform you are running this on:")
    print("\t(1) Raspberry Pi 3B+")
    print("\t(2) Raspberry Pi 4B")
    print("\t(3) Jetson Nano 4GB")
    print("device: ", end="")
    device_name = int(input())
    
    # Start the elapsed time timer
    elapsed_time_start = datetime.datetime.now()
    
    # Define which device will be used
    if(device_name == 1):
        hw_name = "Raspberry Pi 3B+"
    elif(device_name == 2):
        hw_name = "Raspberry Pi 4B"
    elif(device_name == 3):
        hw_name = "Jetson Nano 4GB"
    else:
        raise Exception("You need to enter either 1, 2, or 3... run the program again")
        sys.exit(0)
    
    # Separate initial input in console
    print("\n\nGetting System Information...\n")
    
    
    # Get the hardware information
    hw_info_list = get_hw_info()
    
    # Create the results.txt file header and write hardware info to it
    make_results_txt_header(hw_name)
    push_text("Hardware Information:")
    push_text("\tMachine Type: " + hw_info_list[0])
    push_text("\tProcessor Type: " + hw_info_list[1])
    push_text("\tPhysical Cores: " + str(hw_info_list[2]))
    push_text("\tLogical Cores: " + str(hw_info_list[3]))
    push_text("\tTotal RAM: " + str(hw_info_list[4]) + "GB")
    push_text("\tMax CPU frequency: " + str(hw_info_list[5]) + "MHz")
    
    # Get the software information
    sw_info_list = get_sw_info()
    
    # Write the software info to the results.txt file
    push_text("\nSoftware Information:")
    push_text("\tOperating System: " + sw_info_list[0])
    push_text("\tPython Interpretter: " + sw_info_list[1])
    push_text("\tPython Version: " + sw_info_list[2])
    
    
    # Get execution time of hash verfication
    program_start = datetime.datetime.now()    
    
    
    # Get original.txt file and then hash it with SHA-1 and store its hashed value to .txt file
    print("\nHashing:")
    CHUNK_SIZE = 4096
    sha1 = hashlib.sha1()
    ascii_chunk_list = list()
    with open(original_txt_file_path, 'r') as file:
        while True:
            chunk = file.read(CHUNK_SIZE)
            ascii_chunk_list.append(chunk)
            if chunk:
                sha1.update( bytes(chunk, "ascii") ) 
                push_text(str(sha1.hexdigest()), type="hashes")
            else:
                break
    
    # Write out all hashed values to the console
    for i in range(len(text_to_push_list_hashes)):
        print("Hashed value " + str(i+1) + ": 0x" + str(sha1.hexdigest()))
    
    # Create the actual file for the hashes
    create_txt_file(type="hashes")
    write_txt_file(type="hashes")
    
    # Store associated text chunks to another file --> send.txt
    create_txt_file(type="send")
    write_txt_file(type="send", buffer=ascii_chunk_list)
    
    # Send the data over the network to the receiver
    #transfer_data_to_receiver()

    
    # End execution time tracking
    program_end = datetime.datetime.now()
    elapsed_time_end = datetime.datetime.now()
    
    # split up sections in console
    push_text("\n")
    
    # Calculate the execution time
    execution_time = program_end - program_start
    h,m,s = str(execution_time).split(":")
    execution_time_sec = round(int(h)*3600 + int(m)*60 + float(s), 8)
    
    # Calculate the elapsed time
    elapsed_time = elapsed_time_end - elapsed_time_start
    h,m,s = str(elapsed_time).split(":")
    elapsed_time_sec = round(int(h)*3600 + int(m)*60 + float(s), 8)
    
    # Get average CPU usage over last 1,5,15 minutes
    load_1min, load_5min, load_15min = os.getloadavg()
    cpu_usage_1min = round((load_1min / os.cpu_count()) * 100, 3)
    cpu_usage_5min = round((load_5min / os.cpu_count()) * 100, 3)
    cpu_usage_15min = round((load_15min / os.cpu_count()) * 100, 3)
    
    # Get RAM usage from program based on system call
    max_ram_usage = getrusage(RUSAGE_SELF).ru_maxrss
    
    # Write all information to the results.txt file
    push_text("Execution time = " + str(execution_time_sec) + " seconds")
    push_text("Elapsed time = " + str(elapsed_time_sec) + " seconds")
    push_text("Max RAM usage = " + str(max_ram_usage) + "KB")
    push_text("Average CPU usages (%):")
    push_text("\t1 minute after execution = " + str(cpu_usage_1min) + "%")
    push_text("\t5 minute after execution = " + str(cpu_usage_5min) + "%")
    push_text("\t15 minute after execution = " + str(cpu_usage_15min) + "%")       
    
    # Ask user for input for max and average values from USB power meter
    print("\n\nPlease enter the HIGHEST power draw during process (Watts):  ", end="")
    max_power_draw = round( float(input()), 4 )
    print("Please enter the AVERAGE power draw value during process (Watts):  ", end="")
    avg_power_draw = round( float(input()), 4 )
    print("Please enter the HIGHEST voltage value during the process (Volts):  ", end="")
    max_voltage = round( float(input()), 4 )
    print("Please enter the AVERAGE voltage value during the process (Volts):  ", end="")
    avg_voltage = round( float(input()), 4 )
    print("Please enter the HIGHEST current value during the process (Amps):  ", end="")
    max_current = round( float(input()), 4 )
    print("Please enter the AVERAGE current value during the process (Amps):  ", end="")
    avg_current = round( float(input()), 4 )    
    
    # Put the power values into the results sheet
    push_text("\nElectrical Measurements from the System via USB Power Meter:")
    push_text("\tPeak power: " + str(max_power_draw) + "W")
    push_text("\tAvg power: " + str(avg_power_draw) + "W")
    push_text("\tPeak voltage: " + str(max_voltage) + "V")
    push_text("\tAvg voltage: " + str(avg_voltage) + "V")
    push_text("\tPeak current: " + str(max_current) + "A")
    push_text("\tAvg current: " + str(avg_current) + "A")
    
    
    # Create the actual file for results, then write the results to it
    print("\n\nCreating and writing to .txt file", end="")
    create_txt_file(type="results")
    write_txt_file(type="results")
    print(" Success!")
    
    
    #END
    print("\n\n********************************************************************")
    print("*                                                                  *")
    print("*                        Program complete!!                        *")
    print("*                                                                  *")
    print("********************************************************************")
    

#################################################################################################################
if __name__ == "__main__":
    main()