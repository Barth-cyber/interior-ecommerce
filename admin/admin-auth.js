const e = React.createElement;

function AdminLogin() {
  const [username, setUsername] = React.useState('');
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
        { type: 'submit', disabled: busy, style: { opacity: busy ? 0.7 : 1 } },
        busy ? 'Logging in…' : 'Login'
      )
    ),
    error && e('div', { className: 'error' }, error)
  );
}

ReactDOM.createRoot(document.getElementById('login-root')).render(e(AdminLogin));
