from flask import Flask, request, jsonify
from supabase import create_client
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://wijqrrecsvxdrwdpbbww.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpanFycmVjc3Z4ZHJ3ZHBiYnd3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0MjI1MTMsImV4cCI6MjA5Nzk5ODUxM30.cxi-st7EsjKIscg0Gjr84ysUhLnRoIYJ16bZy6KewKQ')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def home():
    return 'EduLink Backend is running'

@app.route('/validate-voucher', methods=['POST'])
def validate_voucher():
    data = request.json
    code = data.get('code', '').upper()
    hostel = data.get('hostel', '')

    if not code or not hostel:
        return jsonify({'success': False, 'message': 'Code and hostel are required'})

    result = supabase.table('vouchers').select('*').eq('code', code).single().execute()

    if not result.data:
        return jsonify({'success': False, 'message': 'Invalid voucher code'})

    if result.data['used']:
        return jsonify({'success': False, 'message': 'Voucher already used'})

    supabase.table('vouchers').update({'used': True, 'hostel': hostel}).eq('code', code).execute()

    supabase.table('transactions').insert({
        'hostel': hostel,
        'plan': result.data['plan'],
        'amount': result.data['amount'],
        'payment_type': 'voucher',
        'reference': code
    }).execute()

    return jsonify({
        'success': True,
        'plan': result.data['plan'],
        'amount': result.data['amount'],
        'hostel': hostel
    })

@app.route('/log-transaction', methods=['POST'])
def log_transaction():
    data = request.json
    hostel = data.get('hostel', '')
    plan = data.get('plan', '')
    amount = data.get('amount', 0)
    payment_type = data.get('payment_type', '')
    reference = data.get('reference', '')

    if not hostel or not plan or not reference:
        return jsonify({'success': False, 'message': 'Missing required fields'})

    supabase.table('transactions').insert({
        'hostel': hostel,
        'plan': plan,
        'amount': int(amount),
        'payment_type': payment_type,
        'reference': reference
    }).execute()

    return jsonify({'success': True})

@app.route('/recover-session', methods=['POST'])
def recover_session():
    data = request.json
    reference = data.get('reference', '').upper()
    if not reference:
        return jsonify({'success': False, 'message': 'Reference is required'})
    result = supabase.table('transactions').select('*').eq('reference', reference).single().execute()
    if not result.data:
        return jsonify({'success': False, 'message': 'Transaction not found'})
    return jsonify({
        'success': True,
        'plan': result.data['plan'],
        'amount': result.data['amount'],
        'hostel': result.data['hostel']
    })

@app.route('/dashboard', methods=['GET'])
def dashboard():
    result = supabase.table('transactions').select('*').execute()

    if not result.data:
        return jsonify({'success': True, 'hostels': {}, 'transactions': []})

    hostels = {
        'new-male': {'sessions': 0, 'revenue': 0},
        'new-female': {'sessions': 0, 'revenue': 0},
        'abuja': {'sessions': 0, 'revenue': 0},
        'nana': {'sessions': 0, 'revenue': 0}
    }

    for t in result.data:
        if t['hostel'] in hostels:
            hostels[t['hostel']]['sessions'] += 1
            hostels[t['hostel']]['revenue'] += t['amount']

    recent = result.data[-10:]
    recent.reverse()

    return jsonify({
        'success': True,
        'hostels': hostels,
        'transactions': recent
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
