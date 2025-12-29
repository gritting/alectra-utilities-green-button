import sys
import subprocess
import hassapi as hass

class CallScript(hass.Hass):
    def initialize(self):
        event_name = self.args.get("event", "call_script")
        self.listen_event(self.call_script, event_name)
        self.log(f"Listening for '{event_name}' event")

        if self.args.get("run_on_startup", False):
            self.log("Running script on startup...")
            self.call_script()

    def call_script(self, event_name=None, data=None, kwargs=None):
        if "script" not in self.args:
            self.error("Missing script parameter for CallScript")
            return

        script_args = [self.args["script"]]
        if "args" in self.args:
            script_args.extend(self.args["args"])

        self.log(f"Executing script: {' '.join(script_args)}")

        out = sys.stdout
        err = sys.stderr
        closeout = False
        closeerr = False

        if "outfile" in self.args:
            out = open(self.args["outfile"], "w")
            closeout = True
        if "errfile" in self.args:
            err = open(self.args["errfile"], "w")
            closeerr = True

        try:
            result = subprocess.call(script_args, stdout=out, stderr=err)
            self.log(f"Script completed with exit code: {result}")
        except Exception as e: 
            self.error(f"Script execution failed: {e}")
        finally:
            if closeout:
                out.close()
            if closeerr: 
                err.close()