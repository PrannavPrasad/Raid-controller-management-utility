from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

ERROR = 300
SUCCESS = 200
FAILURE = 500
INVALID = 400
NONE = 150

ARCCONF = './arcconfLinux'

class Disk:
    def __init__(self):
        self.disks = {}
    

    def list_storage_controllers(self, returnStatus):
       command = [ARCCONF, 'LIST']
       process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
       output, error = process.communicate()
       if process.returncode == 0:
          controllers = []
          current_controller = {}

          lines = output.decode().splitlines()
          for index, line in enumerate(lines):
              if line.startswith('Controllers 1:'):
                  key = line.strip()
                  value = lines[index + 2].strip()
                  current_controller[key] = value
              elif ':' in line:
                  key, value = line.split(':', 1)
                  current_controller[key.strip()] = value.strip()

          if current_controller:
              controllers.append(current_controller)
              returnStatus["Controller_detail_RAID"] = controllers
              return SUCCESS
          else:
              error_message = "No controller information found"
              print("Error:", error_message)
              returnStatus["statuscode"] = FAILURE
              return FAILURE
       else:
          error_message = process.stderr.strip() if process.stderr else 'Unknown error'
          print("Error:", error_message)
          returnStatus["statuscode"] = FAILURE
          return FAILURE

    def get_disk_info(self, returnStatus):
      controllers = returnStatus["Controller_detail_RAID"]
      print(controllers)
      disks = []
      for controller in controllers:
          controller_info = controller[list(controller.keys())[0]]
          controller_id = controller_info.split(':')[0].strip()
          command = [ARCCONF, 'GETCONFIG', str(controller_id), 'PD']
          print(command)
          process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
          output, error = process.communicate()

          if process.returncode == 0:
              current_disk = {}

              for line in output.decode().splitlines():
                  if line.strip().startswith("Device #"):
                      if current_disk:
                          disks.append(current_disk)
                          current_disk = {}
                      current_disk["Device"] = line.strip()
                      current_disk["Device ID"] = line.strip().split("#")[1].strip()
                  elif ":" in line:
                      key, value = line.split(":", 1)
                      key = key.strip()
                      value = value.strip()
                      if key in ["Device #", "Total Size", "Serial number", "Vendor", "Model", "S.M.A.R.T.", "Reported Channel,Device(T:L)", "Temperature",
                                 "Transfer Speed", "World-wide name", "Write Cache"]:
                          current_disk[key] = value

              if current_disk:
                  disks.append(current_disk)
          else:
              print("Error:", error.decode())
              returnStatus["statuscode"] = FAILURE
              return FAILURE

      if disks:
          returnStatus["statuscode"] = SUCCESS
          returnStatus["disk_details"] = disks
          return SUCCESS
      else:
          error_message = "No disk information found"
          print("Error:", error_message)
          returnStatus["statuscode"] = FAILURE
          return FAILURE



@app.route('/controllers', methods=['GET'])
def cmds():
    args = request.args
    cmd = args.get("cmd", default="NONE", type=str)

    if cmd == "diskinfo":
        returnStatus = {
            "statuscode": "",
            "disk_details": "",
            "Controller_detail_RAID": ""
        }
        diskInfo = Disk()
        returnStatus["statuscode"] = diskInfo.list_storage_controllers(returnStatus)
        if returnStatus["statuscode"] == SUCCESS:
            returnStatus["statuscode"] = diskInfo.get_disk_info(returnStatus)
        return returnStatus

    return "Invalid command"
 
if __name__ == '__main__':
    app.run(host='190.168.1.92', port=12229,debug = True)

