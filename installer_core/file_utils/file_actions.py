from pathlib import Path
from subprocess import run, CalledProcessError, PIPE
from shlex import quote

class FileActions:
    def __init__(self, os_name):
        self.os_name = os_name
        self.operations_log = []
        self.elevated_commands = []  # Commands requiring elevation
        self.non_elevated_commands = []  # Commands not requiring elevation

    def log_operation(self, message):
        """Logs the operation message to the operations log."""
        self.operations_log.append(message)

    def log_to_output_entry(self, output_entry, message):
        """Logs messages to the output entry widget."""
        if output_entry:
            output_entry.configure(state='normal')
            output_entry.insert("end", f"{message}\n")
            output_entry.configure(state='disabled')

    def copy_file(self, source, destination):
        source_path = Path(source)
        destination_path = Path(destination)

        if not source_path.exists():
            self.log_operation(f"Source file does not exist: {source_path}")
            return
        
        command = f'cp {quote(str(source_path))} {quote(str(destination_path))}' if self.os_name.lower() in ["linux", "darwin"] else f'copy "{source_path}" "{destination_path}"'
        self.schedule_command(command, destination_path)

    def move_file(self, source, destination):
        source_path = Path(source)
        destination_path = Path(destination)

        if not source_path.exists():
            self.log_operation(f"Source file does not exist: {source_path}")
            return
        
        command = f'mv {quote(str(source_path))} {quote(str(destination_path))}' if self.os_name.lower() in ["linux", "darwin"] else f'move "{source_path}" "{destination_path}"'
        self.schedule_command(command, destination_path)

    def copy_folder(self, source, destination):
        source_path = Path(source)
        destination_path = Path(destination)

        if not source_path.exists() or not source_path.is_dir():
            self.log_operation(f"Source folder does not exist or is not a directory: {source_path}")
            return
        
        command = f'cp -r {quote(str(source_path))} {quote(str(destination_path))}' if self.os_name.lower() in ["linux", "darwin"] else f'xcopy /e /i "{source_path}" "{destination_path}"'
        self.schedule_command(command, destination_path)

    def move_folder(self, source, destination):
        source_path = Path(source)
        destination_path = Path(destination)

        if not source_path.exists() or not source_path.is_dir():
            self.log_operation(f"Source folder does not exist or is not a directory: {source_path}")
            return
        
        command = f'mv {quote(str(source_path))} {quote(str(destination_path))}' if self.os_name.lower() in ["linux", "darwin"] else f'move "{source_path}" "{destination_path}"'
        self.schedule_command(command, destination_path)

    def remove_file(self, file_path):
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            self.log_operation(f"File does not exist: {path}")
            return
        
        command = f'rm {quote(str(path))}' if self.os_name.lower() in ["linux", "darwin"] else f'del "{path}"'
        self.schedule_command(command, path)

    def remove_folder(self, folder_path):
        path = Path(folder_path)
        if not path.exists() or not path.is_dir():
            self.log_operation(f"Folder does not exist: {path}")
            return
        
        command = f'rm -rf {quote(str(path))}' if self.os_name.lower() in ["linux", "darwin"] else f'rd /s /q "{path}"'
        self.schedule_command(command, path)

    def schedule_command(self, command, path):
        """Schedules the command for execution, deciding if it needs elevation."""
        if self.needs_elevation(path):
            self.elevated_commands.append(command)
        else:
            self.non_elevated_commands.append(command)

    def needs_elevation(self, path):
        """Determines if the operation needs to be elevated based on the target path."""
        if self.os_name.lower() in ["linux", "darwin"]:
            return path.is_absolute() and str(path).startswith("/usr")
        elif self.os_name.lower() == "windows":
            return str(path).startswith("C:\\Program Files")
        return False

    def elevate_commands(self, commands, output_entry):
        """Runs batched commands with elevated permissions."""
        if not commands:
            return

        try:
            if self.os_name.lower() in ["linux", "darwin"]:
                batched_command = " && ".join(commands)
                elevated_command = f'pkexec bash -c "{batched_command}"'
            elif self.os_name.lower() == "windows":
                batched_command = " & ".join(commands)
                elevated_command = f'powershell -Command "Start-Process cmd -ArgumentList \'/c {batched_command}\' -Verb RunAs"'
            else:
                raise NotImplementedError("Elevation not implemented for this OS")

            result = run(elevated_command, shell=True, check=True, stdout=PIPE, stderr=PIPE)
            output = result.stdout.decode('utf-8').strip()
            error = result.stderr.decode('utf-8').strip()

            if output:
                self.log_to_output_entry(output_entry, f"Output: {output}")
            if error:
                self.log_to_output_entry(output_entry, f"Error: {error}")

        except CalledProcessError as e:
            error_message = e.stderr.decode('utf-8').strip()
            self.log_to_output_entry(output_entry, f"Failed to execute elevated commands with error {error_message}")
            # Handle if the user rejects the elevated request
            if "Request dismissed" in error_message:
                self.log_to_output_entry(output_entry, "User denied the elevation request. Installation or removal was not completed.")
        except Exception as e:
            self.log_to_output_entry(output_entry, f"Failed to execute elevated commands with error {e}")

    def execute_operations(self, progress_bar=None, output_entry=None):
        """Executes the batched commands, separating elevated and non-elevated ones."""
        # Check for operations to perform
        if not self.elevated_commands and not self.non_elevated_commands:
            self.log_to_output_entry(output_entry, "No operations to perform.")
            if progress_bar:
                progress_bar.set(1)
            return

        # Execute non-elevated commands first
        for command in self.non_elevated_commands:
            try:
                result = run(command, shell=True, check=True, stdout=PIPE, stderr=PIPE)
                output = result.stdout.decode('utf-8').strip()
                error = result.stderr.decode('utf-8').strip()

                self.log_to_output_entry(output_entry, f"Completed: {command}")
                if output:
                    self.log_to_output_entry(output_entry, f"Output: {output}")
                if error:
                    self.log_to_output_entry(output_entry, f"Error: {error}")

            except CalledProcessError as e:
                self.log_to_output_entry(output_entry, f"Failed: {command} with error {e.stderr.decode('utf-8').strip()}")
            except Exception as e:
                self.log_to_output_entry(output_entry, f"Failed: {command} with error {e}")

        # Insert header for elevated commands
        if self.elevated_commands:
            self.log_to_output_entry(output_entry, "===================Elevated Commands===================")

        # Execute elevated commands in batch
        self.elevate_commands(self.elevated_commands, output_entry)

        # Insert the logs of elevated commands
        if self.elevated_commands:
            for command in self.elevated_commands:
                self.log_to_output_entry(output_entry, f"Executing: {command}")

        # Update progress bar and output entry
        total_operations = len(self.operations_log)
        if output_entry:
            output_entry.configure(state='normal')

        # Insert each logged operation into the output entry
        for i, operation in enumerate(self.operations_log):
            self.log_to_output_entry(output_entry, operation)
            
            # Update progress bar
            progress = (i + 1) / total_operations
            if progress_bar:
                progress_bar.set(progress)
                progress_bar.master.update_idletasks()

        # Final update to mark completion
        if progress_bar:
            progress_bar.set(1)
            progress_bar.master.update_idletasks()

        if output_entry:
            self.log_to_output_entry(output_entry, "All operations completed.")
            output_entry.configure(state='disabled')

        # Clear the operations log and command lists after execution
        self.operations_log.clear()
        self.elevated_commands.clear()
        self.non_elevated_commands.clear()