import os, subprocess, tempfile, json
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort
from functools import wraps
from extensions import db
from models.submission_model import Submission
from models.problem_model import Problem
from models.user_model import User
from sqlalchemy.orm import joinedload
import time
import psutil  # Library untuk mengukur memory usage
import os

sub_bp = Blueprint('submission', __name__, url_prefix='/submissions')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@sub_bp.route('/submit/<pid>', methods=['POST'])
@login_required
def submit(pid):
    try:
        prob = Problem.query.get_or_404(pid)
        user = User.query.get(session['user_id'])
        
        code = request.form.get('code')
        language = request.form.get('language', 'python')
        
        verdicts = []
        max_runtime = 0  # Untuk menyimpan waktu terlama
        max_memory = 0    # Untuk menyimpan memory tertinggi (dalam KB)
        
        with tempfile.TemporaryDirectory() as tmp:
            # Persiapan file
            ext = 'cpp' if language != 'python' else 'py'
            path = os.path.join(tmp, f'sol.{ext}')
            with open(path, 'w') as f:
                f.write(code)
            
            exe = path
            if language != 'python':
                exe = os.path.join(tmp, 'sol')
                compile_result = subprocess.run(
                    ['g++', path, '-std=c++17', '-O2', '-o', exe],
                    capture_output=True
                )
                if compile_result.returncode != 0:
                    verdicts.append({
                        'status': 'Compilation Error',
                        'error': compile_result.stderr.decode()
                    })
            
            if not verdicts:  # Jika kompilasi sukses
                for sample in prob.samples:
                    inp, expected = sample['in'], sample['out'].strip()
                    
                    # Memulai proses
                    start_time = time.time()
                    process = subprocess.Popen(
                        [exe] if language != 'python' else ['python', path],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    try:
                        # Mengukur memory usage
                        memory_usage = 0
                        ps = psutil.Process(process.pid)
                        
                        # Thread untuk memantau memory
                        def monitor_memory():
                            nonlocal memory_usage
                            while process.poll() is None:
                                try:
                                    mem = ps.memory_info().rss / 1024  # dalam KB
                                    if mem > memory_usage:
                                        memory_usage = mem
                                    time.sleep(0.01)
                                except:
                                    break
                        
                        import threading
                        mem_thread = threading.Thread(target=monitor_memory)
                        mem_thread.daemon = True
                        mem_thread.start()
                        
                        # Eksekusi dengan timeout
                        out, err = process.communicate(
                            input=inp.encode(),
                            timeout=2  # timeout 2 detik
                        )
                        
                        runtime = time.time() - start_time
                        out = out.decode().strip()
                        
                        # Update max values
                        if runtime > max_runtime:
                            max_runtime = runtime
                        if memory_usage > max_memory:
                            max_memory = memory_usage
                        
                        status = 'Passed' if out == expected else 'Wrong Answer'
                        verdicts.append({
                            'input': inp,
                            'expected': expected,
                            'got': out,
                            'status': status,
                            'time': f"{runtime:.3f}s",
                            'memory': f"{memory_usage:.1f} KB"
                        })
                        
                    except subprocess.TimeoutExpired:
                        process.kill()
                        runtime = time.time() - start_time
                        verdicts.append({
                            'status': 'Time Limit Exceeded',
                            'time': f"{runtime:.3f}s",
                            'memory': f"{memory_usage:.1f} KB"
                        })
                        
                    except Exception as e:
                        process.kill()
                        runtime = time.time() - start_time
                        verdicts.append({
                            'status': 'Runtime Error',
                            'error': str(e),
                            'time': f"{runtime:.3f}s",
                            'memory': f"{memory_usage:.1f} KB"
                        })
        
        # Format hasil akhir
        runtime_str = f"{max_runtime*1000:.0f} ms" if max_runtime > 0 else '-'
        memory_str = f"{max_memory/1024:.2f} MB" if max_memory > 0 else '-'
        
        # Buat submission
        sub = Submission(
            user_id=user.id,
            problem_id=pid,
            code=code,
            language=language,
            verdicts=verdicts,
            runtime=runtime_str,
            memory=memory_str
        )
        
        db.session.add(sub)
        db.session.commit()
        
        flash(f"Submission #{sub.id}: {sub.verdict_status}", 'success')
        return redirect(url_for('submission.submissions'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Submission failed: {str(e)}', 'error')
        return redirect(url_for('main.problem', pid=pid))
    try:
        prob = Problem.query.get_or_404(pid)
        user = User.query.get(session['user_id'])
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('auth.login'))
            
        code = request.form.get('code')
        language = request.form.get('language', 'python')
        
        if not code:
            flash('No code submitted', 'error')
            return redirect(url_for('main.problem', pid=pid))
        
        verdicts = []
        runtime = '-'
        memory = '-'
        
        # Process submission and get verdicts
        with tempfile.TemporaryDirectory() as tmp:
            ext = 'cpp' if language != 'python' else 'py'
            path = os.path.join(tmp, f'sol.{ext}')
            with open(path, 'w') as f: 
                f.write(code)
                
            exe = path
            if language != 'python':
                exe = os.path.join(tmp, 'sol')
                compile_result = subprocess.run(
                    ['g++', path, '-std=c++17', '-O2', '-o', exe],
                    capture_output=True
                )
                if compile_result.returncode != 0:
                    verdicts.append({
                        'status': 'Compilation Error',
                        'error': compile_result.stderr.decode()
                    })
            
            if not verdicts:  # Only run tests if compilation succeeded
                for sample in prob.samples:
                    inp, expected = sample['in'], sample['out'].strip()
                    try:
                        cmd = [exe] if language != 'python' else ['python', path]
                        result = subprocess.run(
                            cmd,
                            input=inp.encode(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=2
                        )
                        out = result.stdout.decode().strip()
                        status = 'Passed' if out == expected else 'Wrong Answer'
                        verdicts.append({
                            'input': inp,
                            'expected': expected,
                            'got': out,
                            'status': status
                        })
                    except subprocess.TimeoutExpired:
                        verdicts.append({'status': 'Time Limit Exceeded'})
                    except Exception as e:
                        verdicts.append({'status': 'Runtime Error', 'error': str(e)})
        
        # Create submission
        sub = Submission(
            user_id=user.id,
            problem_id=pid,
            code=code,
            language=language,
            verdicts=verdicts,
            runtime=runtime,
            memory=memory
        )
        
        db.session.add(sub)
        db.session.commit()
        
        flash(f"Submission #{sub.id}: {sub.verdict_status}", 'success')
        return redirect(url_for('submission.submissions'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Submission failed: {str(e)}', 'error')
        return redirect(url_for('main.problem', pid=pid))

@sub_bp.route('/')
@login_required
def submissions():
    user_id = session['user_id']
    subs = Submission.query.filter_by(user_id=user_id)\
        .options(
            joinedload(Submission.problem),
            joinedload(Submission.user)
        )\
        .order_by(Submission.timestamp.desc())\
        .all()
    
    return render_template('submissions.html', subs=subs)