/* TaskBoard interactions: all task data is exchanged with the JSON API. */
(() => {
  "use strict";

  const API_URL = "/api/tasks";
  const list = document.getElementById("task-list");
  const taskForm = document.getElementById("task-form");
  const feedback = document.getElementById("feedback-message");
  const statusFilter = document.getElementById("status-filter");
  const priorityFilter = document.getElementById("priority-filter");
  const countElement = document.getElementById("task-count");

  // The script is shared by the base layout, so quietly do nothing off the board.
  if (!list || !taskForm) return;

  let feedbackTimer;

  async function request(url, options = {}) {
    let response;
    try {
      response = await fetch(url, {
        ...options,
        headers: {
          ...(options.body ? { "Content-Type": "application/json" } : {}),
          Accept: "application/json",
          ...options.headers,
        },
      });
    } catch (error) {
      throw new Error("Could not reach the server. Check your connection and try again.");
    }

    if (response.status === 204) return null;

    const contentType = response.headers.get("content-type") || "";
    let payload = null;
    if (contentType.includes("application/json")) {
      try {
        payload = await response.json();
      } catch (error) {
        throw new Error("The server returned an invalid response. Please try again.");
      }
    }

    if (!response.ok) {
      throw new Error(describeApiError(payload, response.status));
    }
    return payload;
  }

  function describeApiError(payload, status) {
    const detail = payload && payload.detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => item && (item.msg || item.message))
        .filter(Boolean);
      if (messages.length) return messages.join(" ");
    }
    if (typeof detail === "string" && detail.trim()) return detail;
    if (status === 404) return "That task could not be found. It may have been removed.";
    if (status === 422) return "Please check the task details and try again.";
    return `The request failed (${status}). Please try again.`;
  }

  function showFeedback(message, isError = false) {
    if (!feedback) return;
    window.clearTimeout(feedbackTimer);
    feedback.textContent = message;
    feedback.classList.toggle("is-error", isError);
    feedback.classList.toggle("error", isError);
    feedback.hidden = false;
    feedbackTimer = window.setTimeout(() => {
      feedback.hidden = true;
    }, isError ? 7000 : 4000);
  }

  function makeElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined && text !== null) element.textContent = String(text);
    return element;
  }

  function setCount(count) {
    if (!countElement) return;
    countElement.textContent = String(count);
    const noun = countElement.parentElement && countElement.parentElement.querySelector("span:last-child");
    if (noun) noun.textContent = count === 1 ? "task" : "tasks";
  }

  function dateLabel(isoDate) {
    // Parsing YYYY-MM-DD as UTC can shift the displayed day in some time zones.
    const [year, month, day] = isoDate.split("-").map(Number);
    const date = new Date(year, month - 1, day);
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "2-digit",
      year: "numeric",
    }).format(date);
  }

  function createTaskCard(task) {
    const completed = Boolean(task.completed);
    const card = makeElement("article", `task-card${completed ? " is-completed" : ""}`);
    card.dataset.taskId = String(task.id);
    card.dataset.completed = String(completed);
    card.dataset.priority = task.priority;

    const toggle = makeElement("button", "completion-toggle");
    toggle.type = "button";
    toggle.setAttribute("aria-label", `Mark ${task.title} as ${completed ? "active" : "completed"}`);
    toggle.setAttribute("aria-pressed", String(completed));
    toggle.title = "Toggle completion";
    toggle.append(makeElement("span", "", completed ? "✓" : ""));
    card.append(toggle);

    const content = makeElement("div", "task-content");
    const display = makeElement("div", "task-display");
    display.append(makeElement("h3", `task-title${completed ? " completed-title" : ""}`, task.title));
    const description = makeElement("p", `task-description${task.description ? "" : " is-empty"}`, task.description || "");
    description.dataset.field = "description";
    description.hidden = !task.description;
    display.append(description);
    content.append(display);

    const editForm = makeElement("form", "task-edit-form");
    editForm.hidden = true;
    editForm.setAttribute("aria-label", "Edit task");

    const titleInput = makeElement("input", "edit-title");
    titleInput.id = `edit-title-${task.id}`;
    titleInput.name = "title";
    titleInput.type = "text";
    titleInput.maxLength = 200;
    titleInput.value = task.title || "";
    titleInput.required = true;
    const titleLabel = makeElement("label", "sr-only", "Task title");
    titleLabel.htmlFor = titleInput.id;
    editForm.append(titleLabel, titleInput);

    const descriptionInput = makeElement("textarea", "edit-description");
    descriptionInput.id = `edit-description-${task.id}`;
    descriptionInput.name = "description";
    descriptionInput.rows = 2;
    descriptionInput.value = task.description || "";
    const descriptionLabel = makeElement("label", "sr-only", "Description");
    descriptionLabel.htmlFor = descriptionInput.id;
    editForm.append(descriptionLabel, descriptionInput);

    const dueInput = makeElement("input", "edit-due-date");
    dueInput.id = `edit-due-date-${task.id}`;
    dueInput.name = "due_date";
    dueInput.type = "date";
    dueInput.value = task.due_date || "";
    const dueLabel = makeElement("label", "sr-only", "Due date");
    dueLabel.htmlFor = dueInput.id;
    editForm.append(dueLabel, dueInput);

    const priorityInput = makeElement("select", "edit-priority");
    priorityInput.id = `edit-priority-${task.id}`;
    priorityInput.name = "priority";
    ["Low", "Medium", "High"].forEach((value) => {
      const option = makeElement("option", "", value);
      option.value = value;
      option.selected = task.priority === value;
      priorityInput.append(option);
    });
    const priorityLabel = makeElement("label", "sr-only", "Priority");
    priorityLabel.htmlFor = priorityInput.id;
    editForm.append(priorityLabel, priorityInput);

    const editActions = makeElement("div", "edit-actions");
    const saveButton = makeElement("button", "button button-primary save-task-button", "Save");
    saveButton.type = "submit";
    const cancelButton = makeElement("button", "button button-secondary cancel-edit-button", "Cancel");
    cancelButton.type = "button";
    editActions.append(saveButton, cancelButton);
    editForm.append(editActions);
    content.append(editForm);

    const meta = makeElement("div", "task-meta");
    meta.append(makeElement("span", `priority-tag priority-${String(task.priority).toLowerCase()}`, `${task.priority} priority`));
    if (task.due_date) {
      const dueDate = makeElement("time", "due-date");
      dueDate.dateTime = task.due_date;
      const icon = makeElement("span", "", "◷");
      icon.setAttribute("aria-hidden", "true");
      dueDate.append(icon, document.createTextNode(` Due ${dateLabel(task.due_date)}`));
      meta.append(dueDate);
    }
    content.append(meta);
    card.append(content);

    const actions = makeElement("div", "task-actions");
    const editButton = makeElement("button", "icon-button edit-task-button", "Edit");
    editButton.type = "button";
    editButton.setAttribute("aria-label", `Edit ${task.title}`);
    editButton.title = "Edit task";
    const deleteButton = makeElement("button", "icon-button delete-task-button", "Delete");
    deleteButton.type = "button";
    deleteButton.setAttribute("aria-label", `Delete ${task.title}`);
    deleteButton.title = "Delete task";
    actions.append(editButton, deleteButton);
    card.append(actions);
    return card;
  }

  function renderTasks(tasks) {
    const fragment = document.createDocumentFragment();
    if (tasks.length === 0) {
      const empty = makeElement("div", "empty-state");
      empty.id = "empty-state";
      const icon = makeElement("span", "empty-state-icon", "✦");
      icon.setAttribute("aria-hidden", "true");
      empty.append(icon, makeElement("h3", "", "No tasks found"));
      empty.append(makeElement("p", "", "Try changing your filters or add a task above."));
      fragment.append(empty);
    } else {
      tasks.forEach((task) => fragment.append(createTaskCard(task)));
    }
    list.replaceChildren(fragment);
    setCount(tasks.length);
  }

  function currentFilters() {
    return {
      status: statusFilter ? statusFilter.value : "all",
      priority: priorityFilter ? priorityFilter.value : "",
    };
  }

  async function refreshTasks() {
    const filters = currentFilters();
    const params = new URLSearchParams();
    if (filters.status && filters.status !== "all") params.set("status", filters.status);
    if (filters.priority) params.set("priority", filters.priority);
    const url = params.size ? `${API_URL}?${params.toString()}` : API_URL;
    const tasks = await request(url);
    if (!Array.isArray(tasks)) throw new Error("The server returned an invalid task list.");
    renderTasks(tasks);
  }

  function setFormBusy(form, busy) {
    form.querySelectorAll("button, input, textarea, select").forEach((control) => {
      control.disabled = busy;
    });
  }

  taskForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!taskForm.reportValidity()) return;

    const title = taskForm.elements.title.value.trim();
    if (!title) {
      taskForm.elements.title.setCustomValidity("Enter a task title.");
      taskForm.elements.title.reportValidity();
      taskForm.elements.title.setCustomValidity("");
      return;
    }

    const data = {
      title,
      description: taskForm.elements.description.value.trim() || null,
      due_date: taskForm.elements.due_date.value || null,
      priority: taskForm.elements.priority.value,
    };
    setFormBusy(taskForm, true);
    try {
      await request(API_URL, { method: "POST", body: JSON.stringify(data) });
      taskForm.reset();
      await refreshTasks();
      showFeedback("Task added.");
    } catch (error) {
      showFeedback(error.message || "Could not add the task.", true);
    } finally {
      setFormBusy(taskForm, false);
    }
  });

  list.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button || !list.contains(button)) return;
    const card = button.closest(".task-card");
    if (!card) return;
    const taskId = card.dataset.taskId;

    if (button.matches(".edit-task-button")) {
      card.querySelector(".task-display").hidden = true;
      card.querySelector(".task-edit-form").hidden = false;
      button.disabled = true;
      const input = card.querySelector(".edit-title");
      input.focus();
      input.select();
      return;
    }

    if (button.matches(".cancel-edit-button")) {
      const form = card.querySelector(".task-edit-form");
      form.reset();
      form.hidden = true;
      card.querySelector(".task-display").hidden = false;
      card.querySelector(".edit-task-button").disabled = false;
      return;
    }

    if (button.matches(".completion-toggle")) {
      button.disabled = true;
      try {
        await request(`${API_URL}/${encodeURIComponent(taskId)}/toggle`, { method: "POST" });
        await refreshTasks();
        showFeedback("Task status updated.");
      } catch (error) {
        button.disabled = false;
        showFeedback(error.message || "Could not update task status.", true);
      }
      return;
    }

    if (button.matches(".delete-task-button")) {
      button.disabled = true;
      try {
        await request(`${API_URL}/${encodeURIComponent(taskId)}`, { method: "DELETE" });
        await refreshTasks();
        showFeedback("Task deleted.");
      } catch (error) {
        button.disabled = false;
        showFeedback(error.message || "Could not delete the task.", true);
      }
    }
  });

  list.addEventListener("submit", async (event) => {
    const form = event.target.closest(".task-edit-form");
    if (!form) return;
    event.preventDefault();
    if (!form.reportValidity()) return;

    const card = form.closest(".task-card");
    const titleInput = form.elements.title;
    const title = titleInput.value.trim();
    if (!title) {
      titleInput.setCustomValidity("Enter a task title.");
      titleInput.reportValidity();
      titleInput.setCustomValidity("");
      return;
    }

    const data = {
      title,
      description: form.elements.description.value.trim() || null,
      due_date: form.elements.due_date.value || null,
      priority: form.elements.priority.value,
    };
    setFormBusy(form, true);
    try {
      await request(`${API_URL}/${encodeURIComponent(card.dataset.taskId)}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      await refreshTasks();
      showFeedback("Task updated.");
    } catch (error) {
      showFeedback(error.message || "Could not update the task.", true);
    } finally {
      // The card may have been replaced after a successful refresh.
      if (form.isConnected) setFormBusy(form, false);
    }
  });

  list.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const form = event.target.closest(".task-edit-form");
    if (!form || form.hidden) return;
    event.preventDefault();
    const card = form.closest(".task-card");
    form.reset();
    form.hidden = true;
    card.querySelector(".task-display").hidden = false;
    const editButton = card.querySelector(".edit-task-button");
    editButton.disabled = false;
    editButton.focus();
  });

  async function filtersChanged() {
    if (statusFilter) statusFilter.disabled = true;
    if (priorityFilter) priorityFilter.disabled = true;
    try {
      await refreshTasks();
    } catch (error) {
      showFeedback(error.message || "Could not load tasks.", true);
    } finally {
      if (statusFilter) statusFilter.disabled = false;
      if (priorityFilter) priorityFilter.disabled = false;
    }
  }

  if (statusFilter) statusFilter.addEventListener("change", filtersChanged);
  if (priorityFilter) priorityFilter.addEventListener("change", filtersChanged);
})();
