"""Local CSS and JavaScript primitives embedded in HTML reports."""

from __future__ import annotations


def html_external_stylesheets() -> str:
    """Return local stylesheet helpers used by the report."""
    return """
  <!-- Local Bootstrap-compatible report primitives -->
  <style id="job-radar-local-report-primitives">
    *, *::before, *::after { box-sizing: border-box; }
    body { margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.5; }
    a { color: #0d6efd; text-decoration: underline; }
    .container { width: min(100% - 2rem, 1140px); margin-inline: auto; }
    .my-4 { margin-block: 1.5rem; }
    .mt-3 { margin-top: 1rem; }
    .mb-0 { margin-bottom: 0; }
    .ms-2 { margin-left: .5rem; }
    .d-inline-block { display: inline-block; }
    .text-center { text-align: center; }
    .text-muted { color: #6c757d; }
    .visually-hidden {
      position: absolute !important; width: 1px !important; height: 1px !important;
      padding: 0 !important; margin: -1px !important; overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important; white-space: nowrap !important; border: 0 !important;
    }
    .alert { padding: 1rem; margin-bottom: 1rem; border: 1px solid transparent; border-radius: .375rem; }
    .alert-info { color: #055160; background: #cff4fc; border-color: #b6effb; }
    .alert-secondary { color: #41464b; background: #e2e3e5; border-color: #d3d6d8; }
    .alert-warning { color: #664d03; background: #fff3cd; border-color: #ffecb5; }
    .btn {
      display: inline-block; padding: .375rem .75rem; border: 1px solid transparent;
      border-radius: .375rem; background: transparent; font: inherit; line-height: 1.5;
      text-align: center; text-decoration: none; cursor: pointer;
    }
    .btn-sm { padding: .25rem .5rem; font-size: .875rem; border-radius: .25rem; }
    .btn-primary { color: #fff; background: #0d6efd; border-color: #0d6efd; }
    .btn-outline-primary { color: #0d6efd; border-color: #0d6efd; }
    .btn-outline-secondary { color: #6c757d; border-color: #6c757d; }
    .btn-outline-success { color: #198754; border-color: #198754; }
    .btn-outline-warning { color: #997404; border-color: #ffc107; }
    .btn-outline-danger { color: #dc3545; border-color: #dc3545; }
    .btn-outline-info { color: #087990; border-color: #0dcaf0; }
    .btn:hover, .btn:focus { filter: brightness(.95); }
    .btn-group { display: inline-flex; flex-wrap: wrap; gap: .25rem; vertical-align: middle; }
    .btn-check { position: absolute; clip: rect(0, 0, 0, 0); pointer-events: none; }
    .btn-check:checked + .btn { color: #fff; background: #6c757d; }
    .dropdown { position: relative; }
    .dropdown-menu {
      display: none; position: absolute; z-index: 1000; min-width: 10rem; padding: .5rem 0;
      margin: .125rem 0 0; list-style: none; background: #fff; border: 1px solid rgba(0,0,0,.15);
      border-radius: .375rem; box-shadow: 0 .5rem 1rem rgba(0,0,0,.15);
    }
    .dropdown-menu-end { right: 0; left: auto; }
    .dropdown.open .dropdown-menu, .dropdown-menu.show { display: block; }
    .dropdown-item { display: block; width: 100%; padding: .25rem 1rem; clear: both; color: #212529; text-decoration: none; white-space: nowrap; }
    .dropdown-item:hover, .dropdown-item:focus { color: #1e2125; background: #e9ecef; }
    .dropdown-divider { height: 0; margin: .5rem 0; overflow: hidden; border-top: 1px solid rgba(0,0,0,.15); }
    .dropdown-toggle::after { display: inline-block; margin-left: .255em; content: ""; border: .3em solid transparent; border-top-color: currentColor; vertical-align: .15em; }
    .table-responsive { overflow-x: auto; }
    .table { width: 100%; margin-bottom: 1rem; color: #212529; border-collapse: collapse; }
    .table > :not(caption) > * > * { padding: .5rem; border-bottom: 1px solid #dee2e6; }
    .table-striped > tbody > tr:nth-of-type(odd) > * { background: rgba(0,0,0,.03); }
    .table-hover > tbody > tr:hover > * { background: rgba(0,0,0,.06); }
    .table-sm > :not(caption) > * > * { padding: .25rem; }
    .notyf-local {
      position: fixed; top: 1rem; right: 1rem; z-index: 2000; max-width: min(24rem, calc(100vw - 2rem));
      padding: .75rem 1rem; border-radius: .375rem; color: #fff; background: #198754;
      box-shadow: 0 .5rem 1rem rgba(0,0,0,.15);
    }
    .notyf-local.error { background: #dc3545; }
  </style>
"""


def html_external_scripts() -> str:
    """Return local script helpers used by the report."""
    return """
  <!-- Local dropdown and toast helpers -->
  <script>
    window.Notyf = window.Notyf || function Notyf() {
      function show(message, type) {
        var node = document.createElement('div');
        node.className = 'notyf-local' + (type === 'error' ? ' error' : '');
        node.setAttribute('role', 'status');
        node.textContent = message;
        document.body.appendChild(node);
        setTimeout(function() { node.remove(); }, 3000);
      }
      this.success = function(message) { show(message, 'success'); };
      this.error = function(message) { show(message, 'error'); };
    };

    document.addEventListener('click', function(event) {
      var toggle = event.target.closest('[data-bs-toggle="dropdown"]');
      document.querySelectorAll('.dropdown.open').forEach(function(dropdown) {
        if (!toggle || !dropdown.contains(toggle)) dropdown.classList.remove('open');
      });
      if (!toggle) return;
      var dropdown = toggle.closest('.dropdown');
      if (!dropdown) return;
      event.preventDefault();
      dropdown.classList.toggle('open');
    });
  </script>
"""
