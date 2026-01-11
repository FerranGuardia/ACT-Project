import re

with open('src/tts/tts_engine.py', 'r') as f:
    content = f.read()

# Replace the RuntimeError block
old_pattern = r'''            # If we get here, we're in an async context but need sync result
            # This should be avoided in GUI apps, but if it happens, raise an error
            # rather than creating threads which can cause deadlocks
            raise RuntimeError\(
                "Cannot run async operation in synchronous context when event loop is already running\. "
                "This operation should be called from a synchronous context only\."
            \)'''

new_replacement = '''            # If we get here, we're in an async context - create a task and wait for it
            if asyncio.iscoroutine(coro):
                task = loop.create_task(coro)
                return loop.run_until_complete(task)
            else:
                # coro is already a task or future
                return loop.run_until_complete(coro)'''

content = re.sub(old_pattern, new_replacement, content, flags=re.MULTILINE | re.DOTALL)

with open('src/tts/tts_engine.py', 'w') as f:
    f.write(content)

print('Fixed AsyncBridge in tts_engine.py')