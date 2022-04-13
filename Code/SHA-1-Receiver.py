####################################################################################
###                                                                              ###
###               ECE 4300 - Computer Architecture Spring 2022                   ###
###   Term Project: SHA-1 Algorithm Performance on Multiple Embedded Platforms   ###
###                                                                              ### 
###                               Receiver Side                                  ###
###                                                                              ###
###            By: Derek Mata, Christopher Yamada, Elizabeth Hwang               ###
###                                                                              ###
####################################################################################

# How to verify a SHA-1 hash: https://askubuntu.com/questions/61826/how-do-i-check-the-sha1-hash-of-a-file

# General python libraries
import sys
import re

# Metric calculating libraries
import platform
import os
import datetime
#from resource import *
import psutil

# Network connection library
import socket



# List to hold all strings to enter into txt file at end
text_to_push_list_results = list()
text_to_push_list_hashes = list()

# Path for results.txt file
HOME_DIR = os.path.dirname(__file__)
results_txt_file_path = os.path.abspath( os.path.join(HOME_DIR, "SHA-1-results-rx.txt") )

# Path for ascii text that will be sent from transmitter
receive_txt_file_path = os.path.abspath( os.path.join(HOME_DIR, "receive.txt") )

# Path for storing hash.txt file stored from the network 
hash_txt_file_path = os.path.abspath( os.path.join(HOME_DIR, "hashes.txt") )

# General path name for storing each hash of each text block
hash_text_block_txt_dir = os.path.abspath(os.path.join(HOME_DIR, "associative-hashes"))
if not os.path.exists(hash_text_block_txt_dir):
    os.mkdir(hash_text_block_txt_dir)

# File to store hashes generated in Linux
linux_hashes_txt_file_path = os.path.abspath(os.path.join(HOME_DIR, "linux-hashes.txt"))



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
    elif(type=="hashes"):
        file = os.open(hash_txt_file_path, os.O_CREAT, 0o777)
    else:
        raise Exception("create_txt_file: type only accepts input of \'hashes\' or \'results\'")
    os.close(file)
    
############################

# Write to text file we store results in
def write_txt_file(type="results") -> None:
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
    else:
        raise Exception("write_txt_file: type only accepts input of \'hashes\' or \'results\'")


#################################
#                               #
#     NETWORK FILE TRANSFER     #
#                               #
#################################
# Create the hashes.txt file and receive.txt
def create_network_passed_files():
    # Create the hashes.txt file
    try:
        if not os.path.exists(hash_txt_file_path):
            os.umask(0)
            file = os.open(hash_txt_file_path, os.O_CREAT, 0o777)
            os.close(file)
    except Exception as e:
        print("Error occurred while making file: " + str(e))
    
    # Create the receive.txt file
    try:
        if not os.path.exists(receive_txt_file_path):
            os.umask(0)
            file = os.open(receive_txt_file_path, os.O_CREAT, 0o777)
            os.close(file)
    except Exception as e:
        print("Error occurred while making file: " + str(e))
   
############################

# Create the client socket and transfer data using utf-8 encoding
def receive_data_from_transmitter(server_ip):
    # Server socket variables
    server_welcome_port = 64321
    RECV_BUFFER = 1024 
    
    # Data buffers for file writing
    data_hashes = list()
    data_receive = list()
    
    # Create TCP welcome socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as welcome_socket:
        # Listen for transmitter, then accept the connection
        welcome_socket.bind((server_ip, server_welcome_port))
        print(f"Listening on {server_ip}:{server_welcome_port} ... ")
        welcome_socket.listen()
        server_connection_socket, _ = welcome_socket.accept()
        print("Connection created, now transferring files")
        
        # Use connection socket to receive hashes.txt and receive.txt
        with server_connection_socket:
            # Set timout to 5 seconds
            server_connection_socket.settimeout(5.0)
            
            # Get hashes.txt file data           
            try:
                while True:
                    data = server_connection_socket.recv(RECV_BUFFER)
                    if not data:
                        break
                    else:
                        data_hashes.append(data)
            except socket.timeout:
                pass
            
            # ACK the transmitter for the hashes.txt file
            server_connection_socket.sendall(b"Successfully received hashes.txt")
    
            # Get receive.txt file data
            try:
                while True:
                    data = server_connection_socket.recv(RECV_BUFFER)
                    if not data:
                        break
                    else:
                        data_receive.append(data)
            except socket.timeout:
                pass
            
            # ACK the transmitter or successfully getting receive.txt
            server_connection_socket.sendall(b"Successfully received receive.txt")              
            
            # Close the connection socket
            server_connection_socket.close()
        
        # Close the welcome socket to TCP server
        welcome_socket.close()
    
    # Write all data to their respective files after closing the socket
    with open(hash_txt_file_path, "wb") as file: 
        for line in data_hashes:
            file.write(line)
        file.close()
    with open(receive_txt_file_path, "wb") as file:               
        for line in data_receive:
            file.write(line)
        file.close()



#################################
#                               #
#         MAIN FUNCTION         #
#                               #
#################################
def main():
    # Start the elapsed time timer
    elapsed_time_start = datetime.datetime.now()
    
    # Get name of embedded device user is running on
    print("Please enter which platform you are running this on:")
    print("\t(1) Raspberry Pi 3B+")
    print("\t(2) Raspberry Pi 4B")
    print("\t(3) Jetson Nano 4GB")
    print("device: ", end="")
    device_name = int(input())

    # Define the device used
    if(device_name == 1):
        hw_name = "Raspberry Pi 3B+"
    elif(device_name == 2):
        hw_name = "Raspberry Pi 4B"
    elif(device_name == 3):
        hw_name = "Jetson Nano 4GB"
    else:
        raise Exception("You need to enter either 1, 2, or 3... run the program again")
        sys.exit(0) 
        
    # Get IP information for this device
    print("\nDevice IP = ", end="")
    server_ip = input()
    reg_ex = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    if not re.match(reg_ex, server_ip):
        raise Exception("Illegal IP address... please retry")
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
    
    # Split up sections
    push_text("\n")
    
    
    # Connect to transmitter over network and receive files
    create_network_passed_files()
    receive_data_from_transmitter(server_ip)
    
    
    # Get execution time of hash verfication
    program_start = datetime.datetime.now()
    
    
    # Run through all hashes stored in the hashes.txt file and store to hashes buffer
    print("Reading hashes and chunks from files...")
    hashes_buffer = list()
    try:
        file = open(hash_txt_file_path, "r")
        for line in file:
            if not line:
                continue
            else:
                hashes_buffer.append(line.split("\n")[0])
    except Exception as e:
        print("Error reading hashes.txt file: " + str(e))
    finally:
        file.close()
        
    # Run through all ascii chunks stored in receive.txt and store to ascii list
    ascii_buffer = list()
    try:
        file = open(receive_txt_file_path, "r")
        for line in file:
            if not line:
                continue
            else:
                ascii_buffer.append(line.split("\n")[0])
    except Exception as e:
        print("Error reading receive.txt file: " + str(e))
    finally:
        file.close()
    
    # Associate each hash with its respective chunk, then make txt file for each ascii chunk
    print("Mapping hashes to its associative text block...")
    hashes_to_text_dict = dict()
    for i in range(len(hashes_buffer)):
        try:
            # Associate hash to text to 1 file
            hashes_to_text_dict.update({str(hashes_buffer[i]): str(ascii_buffer[i])})

            # Make .txt file for this hash
            temp_file_name = "text-of-hashes-" + str(i+1) + ".txt"
            file = open(os.path.join(hash_text_block_txt_dir, temp_file_name), "w+")
            file.write(ascii_buffer[i])            
        except Exception as e:
            print("Error writing to text-of-hashes-" + str(i) +".txt file: " + str(e))
        finally:
            file.close()
    
    # Get linux hash sums from terminal command
    print("Getting hashes from Linux...")
    file = os.open(linux_hashes_txt_file_path, os.O_CREAT, 0o777)
    os.close(file)
    num_hashes = os.listdir(hash_text_block_txt_dir)
    for i in range(len(num_hashes)):
        try:
            print("\tsha1sum " + os.path.join(hash_text_block_txt_dir, num_hashes[i]) + " >> " + linux_hashes_txt_file_path)
            os.system("sha1sum " + os.path.join(hash_text_block_txt_dir, num_hashes[i]) + " >> " + linux_hashes_txt_file_path)
        except Exception as e:
            print("Error in getting hash for " + num_hashes[i] + ": " + str(e))
        
    # Compare hashes in linux by opening the linux hashes file and check if hash was found in dictionary --> if so find it's text file
    print("Comparing hashes...")
    matched_hashes = [False] * len(num_hashes)
    linux_hashes = [None] * len(num_hashes)
    with open(linux_hashes_txt_file_path, "r") as file:
        for raw_line in file:
            line = raw_line.split(" ")[0]
            if(line in hashes_to_text_dict): 
                text_file_number = hashes_buffer.index(line)
                matched_hashes[text_file_number] = True
                print("\tHash match --> " + num_hashes[text_file_number])
            else:
                print("\tHash not found!! --> " + line)                
            linux_hashes[i] = line
    
    # Organize hashes for easier printing to results.txt
    matched_list_for_txt = list()
    for i in range(len(num_hashes)):
        if(matched_hashes[i]):
            matched_list_for_txt.append(num_hashes[i] + " hash has MATCHING value of " + linux_hashes[i])
        else:
            matched_list_for_txt.append(num_hashes[i] + " hash DOES NOT MATCH: \n\thashlib: 0x" + hashes_buffer[i] + "\n\tLinux  : 0x" + str(linux_hashes[i]))
    
    # Write all organized text found to results.txt file
    for line in matched_list_for_txt:
        push_text(line)
    push_text("\n")
    
    
    # End execution and elapsed time tracking
    program_end = datetime.datetime.now()
    elapsed_time_end = datetime.datetime.now()
    
    # Calculate the execution time
    execution_time = program_end - program_start
    h,m,s = str(execution_time).split(":")
    execution_time_sec = round(int(h)*3600 + int(m)*60 + float(s), 8)
    
    # Calculate the elapsed time
    elapsed_time = elapsed_time_end - elapsed_time_start
    h,m,s = str(elapsed_time).split(":")
    elapsed_time_sec = round(int(h)*3600 + int(m)*60 + float(s), 8)
    
    # Get average CPU usage over last 1,5,15 minutes
    # load_1min, load_5min, load_15min = os.getloadavg()
    # cpu_usage_1min = round((load_1min / os.cpu_count()) * 100, 3)
    # cpu_usage_5min = round((load_5min / os.cpu_count()) * 100, 3)
    # cpu_usage_15min = round((load_15min / os.cpu_count()) * 100, 3)
    
    # Get RAM usage from program based on system call
    #max_ram_usage = getrusage(RUSAGE_SELF).ru_maxrss
    
    # Write all information to the results.txt file
    push_text("Execution time = " + str(execution_time_sec) + " seconds")
    push_text("Elapsed time = " + str(elapsed_time_sec) + " seconds")
    #push_text("Max RAM usage = " + str(max_ram_usage) + "KB")
    # push_text("Average CPU usages (%):")
    # push_text("\t1 minute after execution = " + str(cpu_usage_1min) + "%")
    # push_text("\t5 minute after execution = " + str(cpu_usage_5min) + "%")
    # push_text("\t15 minute after execution = " + str(cpu_usage_15min) + "%")       
    
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