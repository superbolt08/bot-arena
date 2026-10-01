"""Subprocess adapter for trusted local bot files. This is not a security sandbox."""
import importlib.util
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    protocol=sys.stdout
    # Bot prints must not corrupt the JSON protocol.
    sys.stdout=sys.stderr
    try:
        path=Path(sys.argv[1]).resolve()
        sys.path.insert(0,str(path.parent))
        spec=importlib.util.spec_from_file_location("student_bot",path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        bot=module.Bot()
        if not callable(getattr(bot,"choose_action",None)):
            raise ValueError("Bot must implement choose_action(observation)")
        protocol.write(json.dumps({"ready":True})+"\n")
        protocol.flush()
        for line in sys.stdin:
            obs=json.loads(line)
            action=bot.choose_action(obs)
            protocol.write(json.dumps({"action":action})+"\n")
            protocol.flush()
    except Exception as exc:
        protocol.write(json.dumps({"error":str(exc)[:300]})+"\n")
        protocol.flush()
        traceback.print_exc(file=sys.stderr)


if __name__=="__main__": main()
