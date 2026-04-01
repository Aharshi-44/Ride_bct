(function () {
  function getCookie(name) {
    var v = document.cookie.match("(^|;) ?" + name + "=([^;]*)(;|$)");
    return v ? decodeURIComponent(v[2]) : "";
  }

  var modal = document.getElementById("wait-modal");
  if (!modal) return;

  var pollTimer = null;
  var currentRideId = null;
  var wasAccepted = false;

  function statusApiUrl(rideId) {
    return "/rides/" + rideId + "/status/api/";
  }

  function riderCancelUrl(rideId) {
    return "/rides/" + rideId + "/rider-cancel/";
  }

  function paymentUrl(rideId) {
    return "/rides/" + rideId + "/payment/";
  }

  function showWaitPanel(which) {
    ["loading", "accepted", "cancelled"].forEach(function (name) {
      var el = document.getElementById("wait-panel-" + name);
      if (el) el.classList.toggle("hidden", name !== which);
    });
  }

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function applyPayload(data) {
    var st = data.status;
    if (st === "pending") {
      showWaitPanel("loading");
      return;
    }
    if (st === "accepted") {
      wasAccepted = true;
      showWaitPanel("accepted");
      var name = data.driver_name || "Driver";
      var vehicle = data.vehicle_number || "—";
      var msg = document.getElementById("wait-accepted-msg");
      var vline = document.getElementById("wait-vehicle-line");
      var pay = document.getElementById("wait-btn-payment");
      if (msg) {
        msg.textContent = "Ride accepted by " + name + ".";
      }
      if (vline) {
        vline.textContent = "Vehicle: " + vehicle;
      }
      if (pay && currentRideId) {
        pay.href = paymentUrl(currentRideId);
      }
      return;
    }
    if (st === "cancelled") {
      stopPoll();
      showWaitPanel("cancelled");
      var cmsg = document.getElementById("wait-cancelled-msg");
      if (cmsg) {
        cmsg.textContent = wasAccepted
          ? "Your driver cancelled this ride."
          : "This ride was cancelled.";
      }
      return;
    }
    if (st === "ongoing" || st === "completed") {
      stopPoll();
      if (currentRideId) {
        window.location.href = "/rides/" + currentRideId + "/status/";
      }
      return;
    }
    showWaitPanel("loading");
  }

  function pollOnce() {
    if (!currentRideId) return;
    fetch(statusApiUrl(currentRideId), {
      credentials: "same-origin",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (data.error) return;
        applyPayload(data);
      })
      .catch(function () {});
  }

  function startPolling(rideId) {
    stopPoll();
    currentRideId = rideId;
    wasAccepted = false;
    showWaitPanel("loading");
    pollOnce();
    pollTimer = setInterval(pollOnce, 2500);
  }

  function openModal(rideId) {
    if (!modal) return;
    modal.classList.remove("hidden");
    document.documentElement.classList.add("modal-open");
    startPolling(rideId);
  }

  function closeModal() {
    stopPoll();
    currentRideId = null;
    wasAccepted = false;
    if (modal) modal.classList.add("hidden");
    document.documentElement.classList.remove("modal-open");
    showWaitPanel("loading");
  }

  function csrfToken() {
    var t = getCookie("csrftoken");
    if (t) return t;
    var inp = document.querySelector("[name=csrfmiddlewaretoken]");
    return inp ? inp.value : "";
  }

  var btnRiderCancel = document.getElementById("wait-btn-rider-cancel");
  if (btnRiderCancel) {
    btnRiderCancel.addEventListener("click", function () {
      if (!currentRideId) return;
      var csrftoken = csrfToken();
      fetch(riderCancelUrl(currentRideId), {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
        },
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (data) {
          if (data.ok) {
            wasAccepted = false;
            stopPoll();
            showWaitPanel("cancelled");
            var cmsg = document.getElementById("wait-cancelled-msg");
            if (cmsg) cmsg.textContent = "You cancelled this request.";
          }
        })
        .catch(function () {});
    });
  }

  var btnClose = document.getElementById("wait-btn-close");
  if (btnClose) {
    btnClose.addEventListener("click", closeModal);
  }

  window.VeloraWaitModal = { open: openModal, close: closeModal };

  document.addEventListener("DOMContentLoaded", function () {
    var wid = window.__VELORA_WAIT_RIDE_ID__;
    if (wid) {
      openModal(wid);
    }
  });
})();
