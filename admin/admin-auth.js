const e = React.createElement;

function AdminLogin() {
  const [username, setUsername] = React.useState('admin');
  const [password, setPassword] = React.useState('');
  const [error, setError] = React.useState('');
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    fetch('/api/session', { credentials: 'same-origin' })
      .then((res) => res.json())
      .then((data) => {
        if (data.logged_in) {
          window.location.href = '/admin';
        }
      })
      .catch(() => {});
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        window.location.href = '/admin';
        return;
      }

      const data = await response.json();
      setError(data.error || 'Invalid credentials');
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return e(
    'div',
    { className: 'login-container' },
    e('h1', null, 'Admin Login'),
    e('div', { style: { backgroundColor: '#f9f9f9', padding: '1rem', borderRadius: '4px', marginBottom: '1.5rem', fontSize: '0.9rem', lineHeight: '1.6', color: '#333' } },
      e('strong', null, 'Secure admin access'),
      e('p', { style: { margin: '0.5rem 0 0' } }, 'Enter the configured admin username and password. If this site is deployed, make sure environment credentials are set via ADMIN_USERNAME and ADMIN_PASSWORD or ADMIN_PASSWORD_HASH.')
    ),
    e(
      'form',
      { onSubmit: handleSubmit },
      e('label', { htmlFor: 'username' }, 'Username:'),
      e('input', {
        id: 'username',
        name: 'username',
        type: 'text',
        required: true,
        value: username,
        onChange: (e) => setUsername(e.target.value),
      }),
      e('label', { htmlFor: 'password' }, 'Password:'),
      e('input', {
        id: 'password',
        name: 'password',
        type: 'password',
        required: true,
        value: password,
        onChange: (e) => setPassword(e.target.value),
      }),
      e(
        'button',
        { type: 'submit', disabled: busy, style: { opacity: busy ? 0.7 : 1, cursor: busy ? 'not-allowed' : 'pointer' } },
        busy ? 'Logging in…' : 'Login'
      )
    ),
    error && e('div', { className: 'error', style: { marginTop: '1rem', padding: '0.75rem', backgroundColor: '#fee', borderRadius: '4px', border: '1px solid #fcc' } }, error)
  );
}

ReactDOM.createRoot(document.getElementById('login-root')).render(e(AdminLogin));
