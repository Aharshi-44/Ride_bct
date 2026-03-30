(function () {
  var root = document.documentElement;
  var key = 'velora-theme';

  function apply(stored) {
    if (stored === 'dark') root.classList.add('dark');
    else if (stored === 'light') root.classList.remove('dark');
    else if (window.matchMedia('(prefers-color-scheme: dark)').matches) root.classList.add('dark');
    else root.classList.remove('dark');
  }

  apply(localStorage.getItem(key));

  var btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', function () {
      var dark = root.classList.toggle('dark');
      localStorage.setItem(key, dark ? 'dark' : 'light');
    });
  }

  var toastRoot = document.getElementById('toast-root');
  if (toastRoot) {
    document.querySelectorAll('[data-toast]').forEach(function (el) {
      el.classList.add(
        'pointer-events-auto',
        'max-w-sm',
        'rounded-xl',
        'glass',
        'px-4',
        'py-3',
        'shadow-lg',
        'animate-[fadeIn_0.3s_ease-out]'
      );
      toastRoot.appendChild(el);
      setTimeout(function () {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.4s';
        setTimeout(function () { el.remove(); }, 400);
      }, 4500);
    });
  }
})();
