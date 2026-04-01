(function () {
  var root = document.querySelector("[data-ride-status-root]");
  if (!root) return;
  var url = root.getAttribute("data-poll-url");
  var initialStatus = root.getAttribute("data-initial-status") || "pending";
  var isRider = root.getAttribute("data-viewer-is-rider") === "1";
  if (!url) return;

  var bar = document.getElementById("progress-bar");
  var badge = document.getElementById("status-badge");
  var driverName = document.getElementById("driver-name");
  var vehicleNum = document.getElementById("vehicle-num");
  var fareDisplay = document.getElementById("fare-display");
  var pickupText = document.getElementById("pickup-text");
  var dropText = document.getElementById("drop-text");
  var avatar = document.getElementById("driver-avatar");
  var cancelledNotice = document.getElementById("cancelled-notice");
  var updatesMsg = document.getElementById("status-updates-msg");
  var pollId = null;

  var labels = {
    pending: "Pending",
    accepted: "Accepted",
    ongoing: "Ongoing",
    completed: "Completed",
    cancelled: "Cancelled",
  };

  function widthFor(status) {
    switch (status) {
      case "pending":
        return "25%";
      case "accepted":
        return "50%";
      case "ongoing":
        return "75%";
      case "completed":
        return "100%";
      case "cancelled":
        return "0%";
      default:
        return "25%";
    }
  }

  function highlightStages(status) {
    var order = ["pending", "accepted", "ongoing", "completed"];
    var idx = order.indexOf(status);
    document.querySelectorAll("#stage-labels [data-stage]").forEach(function (el) {
      var s = el.getAttribute("data-stage");
      var i = order.indexOf(s);
      var active = status !== "cancelled" && i <= idx && idx >= 0;
      el.classList.toggle("stage--active", active);
    });
  }

  function applyCancelledUi() {
    if (cancelledNotice) {
      cancelledNotice.classList.remove("hidden");
      cancelledNotice.innerHTML = isRider
        ? "<strong>Ride cancelled.</strong> Your driver cancelled this trip. You can book another ride from your dashboard."
        : "<strong>Ride cancelled.</strong> You cancelled this trip.";
    }
    if (badge) {
      badge.textContent = "Cancelled";
      badge.classList.add("status-pill--danger");
    }
    if (bar) bar.style.width = "0%";
    if (updatesMsg) updatesMsg.textContent = "This trip did not complete.";
    highlightStages("cancelled");
  }

  function tick() {
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" }, credentials: "same-origin" })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (data.error) return;
        var st = data.status;
        if (st === "cancelled") {
          applyCancelledUi();
          if (pollId !== null) {
            clearInterval(pollId);
            pollId = null;
          }
          return;
        }
        if (bar) bar.style.width = widthFor(st);
        if (badge) {
          badge.textContent = labels[st] || st;
          badge.classList.remove("status-pill--danger");
        }
        if (driverName) driverName.textContent = data.driver_name || "Matching…";
        if (vehicleNum) vehicleNum.textContent = data.vehicle_number || "—";
        if (fareDisplay) fareDisplay.textContent = "₹" + data.fare;
        if (pickupText) pickupText.textContent = data.pickup_location;
        if (dropText) dropText.textContent = data.drop_location;
        if (avatar && data.driver_name) {
          avatar.textContent = data.driver_name.charAt(0).toUpperCase();
        }
        highlightStages(st);
      })
      .catch(function () {});
  }

  if (initialStatus === "cancelled") {
    applyCancelledUi();
  } else {
    highlightStages(initialStatus);
    pollId = setInterval(tick, 3000);
    tick();
  }
})();
