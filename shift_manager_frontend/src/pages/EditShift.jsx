import { useEffect, useState } from "react";
import { Calendar, dateFnsLocalizer, Views } from "react-big-calendar";
import format from "date-fns/format";
import parse from "date-fns/parse";
import startOfWeek from "date-fns/startOfWeek";
import getDay from "date-fns/getDay";
import "react-big-calendar/lib/css/react-big-calendar.css";
import enUS from "date-fns/locale/en-US";
import { useTransitionPoller } from "../hooks/useTransitionPoller";

const locales = { "en-US": enUS };

const localizer = dateFnsLocalizer({
    format,
    parse,
    startOfWeek,
    getDay,
    locales,
});
function utcToLocal(utcString) {
    const date = new Date(utcString);
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000);
}

function EditShift() {
    useTransitionPoller(); 
    const [events, setEvents] = useState([]);
    const [view, setView] = useState(Views.WEEK);
    const [date, setDate] = useState(new Date());
    const [selectedShift, setSelectedShift] = useState(null);
    const [error, setError] = useState(null);
    const [showTemplateSelector, setShowTemplateSelector] = useState(false);
    const [savedTemplates, setSavedTemplates] = useState([]);
    const [showTemplateForm, setShowTemplateForm] = useState(false);
    const [newTemplate, setNewTemplate] = useState({
        title: "",
        planned_start: "08:00",
        planned_end: "16:00",
        break1_start: "",
        break1_end: "",
        lunch_start: "",
        lunch_end: "",
        break2_start: "",
        break2_end: "",
        target_cycle_time: 60,
    });
  
    useEffect(() => {
        fetchShifts();
    }, []);
   
    
    async function saveNewTemplate() {
        if (!newTemplate.title.trim()) {
            alert("❌ Title is required.");
            return;
        }

        try {
            const res = await fetch("/api/save_template", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(newTemplate),
            });

            if (!res.ok) throw new Error("Failed to save template");
            const saved = await res.json();
            console.log("✅ Template saved:", saved);

            setShowTemplateForm(false);
            setNewTemplate({
                title: "shift",
                planned_start: "08:00",
                planned_end: "16:00",
                break1_start: "",
                break1_end: "",
                lunch_start: "",
                lunch_end: "",
                break2_start: "",
                break2_end: "",
                target_cycle_time: 60,
            });

            fetchSavedTemplates?.();  // Optional refresh
        } catch (err) {
            console.error("❌ Error saving template:", err);
        }
    }
    async function fetchShifts() {
        try {
            const res = await fetch("/api/planned_shifts");
            if (!res.ok) throw new Error("Failed to load shifts");
            const data = await res.json();
            console.log(res);
            const formatted = data.map((shift) => ({
                id: shift.id,
                title: `Shift ${shift.id}`,
                start: utcToLocal(shift.start_time),
                end: utcToLocal(shift.end_time),
                break1_start: shift.break1_start ? utcToLocal(shift.break1_start) : null,
                break1_end: shift.break1_end ? utcToLocal(shift.break1_end) : null,
                lunch_start: shift.lunch_start ? utcToLocal(shift.lunch_start) : null,
                lunch_end: shift.lunch_end ? utcToLocal(shift.lunch_end) : null,
                break2_start: shift.break2_start ? utcToLocal(shift.break2_start) : null,
                break2_end: shift.break2_end ? utcToLocal(shift.break2_end) : null,
                target_cycle_time: shift.target_cycle_time || null,
            }));

            setEvents(formatted);
        } catch (err) {
            console.error(err);
        }
    }
    async function fetchSavedTemplates() { // grab saved shift templates
        try {
            const res = await fetch("/api/saved_shifts");
            if (!res.ok) throw new Error("Failed to load");
            const data = await res.json();
            setSavedTemplates(data);

        } catch (err) {
            console.log("ye ye", err);
        }
    }
    function handleSelectEvent(event) {
        setSelectedShift(event);
    }

    async function handleSaveShift(shift) {
        try {
            setError(null); // reset previous error
            const url =
                shift.id === "new"
                    ? "/api/create_shift"
                    : `/api/update_shift/${shift.id}`;

            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: shift.title,
                    start: shift.start.toISOString(),
                    end: shift.end.toISOString(),
                    break1_start: shift.break1_start ? shift.break1_start.toISOString() : null,
                    break1_end: shift.break1_end ? shift.break1_end.toISOString() : null,
                    lunch_start: shift.lunch_start ? shift.lunch_start.toISOString() : null,
                    lunch_end: shift.lunch_end ? shift.lunch_end.toISOString() : null,
                    break2_start: shift.break2_start ? shift.break2_start.toISOString() : null,
                    break2_end: shift.break2_end ? shift.break2_end.toISOString() : null,
                    target_cycle_time: shift.target_cycle_time || null,
                }),
            });

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(errorText || "Failed to save shift");
            }

            setSelectedShift(null);
            fetchShifts(); // refresh calendar
        } catch (err) {
            console.error(err);
            setError(err.message); // 👈 Send to user-facing error
        }
    }


    async function handleDeleteShift(id) {
        try {
            const res = await fetch(`/api/delete_shift/${id}`, {
                method: "DELETE",
            });

            if (!res.ok) throw new Error("Failed to delete shift");

            setSelectedShift(null);
            fetchShifts();
        } catch (err) {
            console.error(err);
        }
    }

    function toLocalDatetimeInputString(timestamp) {
        if (!timestamp) return "";

        // If it's already a Date object, format it directly
        const date = timestamp instanceof Date ? timestamp : new Date(timestamp);

        const pad = (n) => String(n).padStart(2, "0");

        const year = date.getFullYear();
        const month = pad(date.getMonth() + 1);
        const day = pad(date.getDate());
        const hours = pad(date.getHours());
        const minutes = pad(date.getMinutes());

        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    return (
        <div className="p-2">
            <button
                onClick={() => (window.location.href = "/")}
                style={{
                    background: "#ccc",
                    border: "1px solid #999",
                    padding: "0.4rem 0.8rem",
                    borderRadius: "2px",
                    cursor: "pointer",
                    marginBottom: "1rem"
                }}
            >
                ← Back to Home
            </button>
            <h2 className="text-2xl font-bold mb-4">Edit Shifts</h2>
            <div style={{ position: "relative" }}>
                <button
                    onClick={() =>
                        setSelectedShift({
                            id: "new",
                            title: "New Shift",
                            start: new Date(),
                            end: new Date(new Date().getTime() + 4 * 60 * 60 * 1000),
                            break1_start: null,
                            break1_end: null,
                            lunch_start: null,
                            lunch_end: null,
                            break2_start: null,
                            break2_end: null,
                            target_cycle_time: 60
                        })
                    }
                    style={{
                        position: "absolute",
                        top: ".000000001%",
                        right: "81%",
                        background: "black",
                        color: "white",
                        border: "none",
                        borderRadius: "6px",
                        padding: "0.5rem 1rem",
                        fontSize: "1rem",
                        cursor: "pointer",
                        zIndex: 20,
                    }}
                >
                    ➕ Plan New Shift
                </button>

                <Calendar
                    localizer={localizer}
                    events={events}
                    startAccessor="start"
                    endAccessor="end"
                    date={date}
                    onNavigate={(newDate) => setDate(newDate)}
                    defaultDate={new Date()}
                    view={view}
                    onView={(newView) => setView(newView)}
                    views={[Views.MONTH, Views.WEEK, Views.DAY, Views.AGENDA]}
                    style={{ height: "80vh", width: "100%" }}
                    onSelectEvent={handleSelectEvent}
                />
                {showTemplateSelector && (
                    <div style={{
                        position: "absolute",
                        top: 0,
                        right: 0,
                        width: "400px",
                        height: "100%",
                        background: "white",
                        borderLeft: "1px solid #ccc",
                        padding: "1rem",
                        overflowY: "auto",
                        boxShadow: "-4px 0 8px rgba(0,0,0,0.1)",
                        zIndex: 20
                    }}>
                        <h3>Saved Shift Templates</h3>

                        {/* Create New Template Button */}
                        {!showTemplateForm && (
                            <button
                                onClick={() => setShowTemplateForm(true)}
                                style={{
                                    background: "#007bff",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "4px",
                                    padding: "0.4rem 0.8rem",
                                    marginBottom: "1rem",
                                    cursor: "pointer"
                                }}
                            >
                                ➕ Create New Template
                            </button>
                        )}
                        {showTemplateForm && (
                            <div style={{ marginBottom: "1rem", borderBottom: "1px solid #ddd", paddingBottom: "1rem" }}>
                                <label>Title:
                                    <input
                                        type="text"
                                        value={newTemplate.title}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, title: e.target.value })}
                                        required
                                    />
                                </label><br />

                                <label>Start:
                                    <input
                                        type="time"
                                        value={newTemplate.planned_start}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, planned_start: e.target.value })}
                                    />
                                </label><br />

                                <label>End:
                                    <input
                                        type="time"
                                        value={newTemplate.planned_end}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, planned_end: e.target.value })}
                                    />
                                </label><br />

                                <label>Break 1 Start:
                                    <input
                                        type="time"
                                        value={newTemplate.break1_start}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, break1_start: e.target.value })}
                                    />
                                </label><br />

                                <label>Break 1 End:
                                    <input
                                        type="time"
                                        value={newTemplate.break1_end}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, break1_end: e.target.value })}
                                    />
                                </label><br />

                                <label>Lunch Start:
                                    <input
                                        type="time"
                                        value={newTemplate.lunch_start}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, lunch_start: e.target.value })}
                                    />
                                </label><br />

                                <label>Lunch End:
                                    <input
                                        type="time"
                                        value={newTemplate.lunch_end}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, lunch_end: e.target.value })}
                                    />
                                </label><br />

                                <label>Break 2 Start:
                                    <input
                                        type="time"
                                        value={newTemplate.break2_start}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, break2_start: e.target.value })}
                                    />
                                </label><br />

                                <label>Break 2 End:
                                    <input
                                        type="time"
                                        value={newTemplate.break2_end}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, break2_end: e.target.value })}
                                    />
                                </label><br />

                                <label>Cycle Time (s):
                                    <input
                                        type="number"
                                        value={newTemplate.target_cycle_time}
                                        onChange={(e) => setNewTemplate({ ...newTemplate, target_cycle_time: parseInt(e.target.value) || 0 })}
                                    />
                                </label><br /><br />

                                <button onClick={saveNewTemplate} style={{
                                    background: "green", color: "white", border: "none", borderRadius: "4px",
                                    padding: "0.4rem 0.8rem", marginRight: "0.5rem", cursor: "pointer"
                                }}>
                                    💾 Save Template
                                </button>

                                <button onClick={() => setShowTemplateForm(false)} style={{
                                    background: "#aaa", color: "white", border: "none", borderRadius: "4px",
                                    padding: "0.4rem 0.8rem", cursor: "pointer"
                                }}>
                                    ✖ Cancel
                                </button>
                            </div>
                        )}

                        {/* List of Templates */}
                        <ul style={{ listStyle: "none", padding: 0 }}>
                            {savedTemplates.map((template) => (
                                <li key={template.id} style={{ marginBottom: "1rem", borderBottom: "1px solid #ddd", paddingBottom: "1rem" }}>
                                    <div style={{ fontWeight: "bold" }}>{template.title}</div>
                                    <div>Start: {template.planned_start} – End: {template.planned_end}</div>

                                    <button
                                        onClick={() => {
                                            const today = new Date();
                                            const todayStr = today.toISOString().split("T")[0];

                                            const toDateTime = (timeStr) => {
                                                if (!timeStr) return null;

                                                const fullStr = `${todayStr} ${timeStr}`;
                                                const parsed = new Date(fullStr);

                                                if (isNaN(parsed)) {
                                                    const [time, modifier] = timeStr.split(" ");
                                                    let [hours, minutes] = time.split(":").map(Number);
                                                    if (modifier === "PM" && hours < 12) hours += 12;
                                                    if (modifier === "AM" && hours === 12) hours = 0;
                                                    return new Date(today.getFullYear(), today.getMonth(), today.getDate(), hours, minutes);
                                                }

                                                return parsed;
                                            };

                                            console.log("📋 Template times parsed:", {
                                                start: toDateTime(template.planned_start),
                                                end: toDateTime(template.planned_end)
                                            });

                                            setSelectedShift({
                                                id: "new",
                                                title: template.title,
                                                start: toDateTime(template.planned_start),
                                                end: toDateTime(template.planned_end),
                                                break1_start: toDateTime(template.break1_start),
                                                break1_end: toDateTime(template.break1_end),
                                                lunch_start: toDateTime(template.lunch_start),
                                                lunch_end: toDateTime(template.lunch_end),
                                                break2_start: toDateTime(template.break2_start),
                                                break2_end: toDateTime(template.break2_end),
                                                target_cycle_time: template.target_cycle_time,
                                            });

                                            setShowTemplateSelector(false);
                                        }}
                                        style={{
                                            marginTop: "0.5rem",
                                            background: "#0066cc",
                                            color: "white",
                                            border: "none",
                                            borderRadius: "4px",
                                            padding: "0.4rem 0.8rem",
                                            cursor: "pointer"
                                        }}
                                    >
                                        Use This Template
                                    </button>
                                </li>
                            ))}
                        </ul>

                        <button
                            onClick={() => setShowTemplateSelector(false)}
                            style={{
                                marginTop: "1rem",
                                background: "#eee",
                                border: "1px solid #ccc",
                                borderRadius: "4px",
                                padding: "0.4rem 0.8rem",
                                cursor: "pointer"
                            }}
                        >
                            ← Back
                        </button>
                    </div>
                )}
                {selectedShift && (
                    <div style={{
                        position: "absolute",
                        top: 0,
                        right: 0,
                        width: "400px",
                        height: "100%",
                        background: "white",
                        borderLeft: "1px solid #ccc",
                        padding: "1rem",
                        overflowY: "auto",
                        boxShadow: "-4px 0 8px rgba(0,0,0,0.1)",
                        zIndex: 10
                    }}>
                        <h3>
                            {selectedShift.id === "new" ? "Plan a New Shift" : `Edit Shift ${selectedShift.id}`}
                        </h3>

                        {/* Top-right Select Saved Shift button */}
                        {selectedShift.id === "new" && (
                            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "1rem" }}>
                                <button
                                    onClick={() => {
                                        fetchSavedTemplates();
                                        setShowTemplateSelector(true);
                                    }}
                                    style={{
                                        background: "#444",
                                        color: "white",
                                        border: "none",
                                        borderRadius: "4px",
                                        padding: "0.4rem 0.8rem",
                                        fontSize: "0.9rem",
                                        cursor: "pointer"
                                    }}
                                >
                                    📂 Select Saved Shift
                                </button>
                            </div>
                        )}


                        {error && (
                            <div style={{
                                color: "red",
                                marginBottom: "1rem",
                                fontWeight: "bold",
                                background: "#ffe6e6",
                                padding: "0.5rem",
                                borderRadius: "6px"
                            }}>
                                {error}
                            </div>
                        )}

                        <label>
                            Title:
                            <input
                                type="text"
                                value={selectedShift.title}
                                onChange={(e) =>
                                    setSelectedShift({ ...selectedShift, title: e.target.value })
                                }
                            />
                        </label>

                        <br />
                        <label>
                            Cycle Time (s):
                            <input
                                type="number"
                                value={selectedShift.target_cycle_time || ""}
                                onChange={(e) =>
                                    setSelectedShift({
                                        ...selectedShift,
                                        target_cycle_time: parseFloat(e.target.value),
                                    })
                                }
                                min="1"
                                step="1"
                            />
                        </label>
                        <br />

                        <label>
                            Start:
                            <input
                                type="datetime-local"
                                value={toLocalDatetimeInputString(selectedShift.start)}
                                onChange={(e) =>
                                    setSelectedShift({
                                        ...selectedShift,
                                        start: new Date(e.target.value),
                                    })
                                }
                            />
                        </label>
                        <br />

                        <label>
                            End:
                            <input
                                type="datetime-local"
                                value={toLocalDatetimeInputString(selectedShift.end)}
                                onChange={(e) =>
                                    setSelectedShift({
                                        ...selectedShift,
                                        end: new Date(e.target.value),
                                    })
                                }
                            />
                        </label>
                        <br /><br />

                        <label>
                            Break 1 Start:
                            <input
                                type="datetime-local"
                                value={toLocalDatetimeInputString(selectedShift.break1_start)}
                                onChange={(e) =>
                                    setSelectedShift({
                                        ...selectedShift,
                                        break1_start: e.target.value ? new Date(e.target.value) : null,
                                    })
                                }
                            />
                        </label>
                        <br />
                        <label>
                            Break 1 End:
                            <input
                                type="datetime-local"
                                value={toLocalDatetimeInputString(selectedShift.break1_end)}
                                onChange={(e) =>
                                    setSelectedShift({
                                        ...selectedShift,
                                        break1_end: e.target.value ? new Date(e.target.value) : null,
                                    })
                                }
                            />
                        </label>
                        <br /><br />

                        <label>
                            Lunch Start:
                            <input
                                type="datetime-local"
                                value={toLocalDatetimeInputString(selectedShift.lunch_start)}
                                onChange={(e) =>
                                    setSelectedShift({
                                        ...selectedShift,
                                        lunch_start: e.target.value ? new Date(e.target.value) : null,
                                    })
                                }
                            />
                        </label>
                        <br />
                        <label>
                            Lunch End:
                            <input
                                type="datetime-local"
                                value={toLocalDatetimeInputString(selectedShift.lunch_end)}
                                onChange={(e) =>
                                    setSelectedShift({
                                        ...selectedShift,
                                        lunch_end: e.target.value ? new Date(e.target.value) : null,
                                    })
                                }
                            />
                        </label>
                        <br /><br />

                        <label>
                            Break 2 Start:
                            <input
                                type="datetime-local"
                                value={toLocalDatetimeInputString(selectedShift.break2_start)}
                                onChange={(e) =>
                                    setSelectedShift({
                                        ...selectedShift,
                                        break2_start: e.target.value ? new Date(e.target.value) : null,
                                    })
                                }
                            />
                        </label>
                        <br />
                        <label>
                            Break 2 End:
                            <input
                                type="datetime-local"
                                value={toLocalDatetimeInputString(selectedShift.break2_end)}
                                onChange={(e) =>
                                    setSelectedShift({
                                        ...selectedShift,
                                        break2_end: e.target.value ? new Date(e.target.value) : null,
                                    })
                                }
                            />
                        </label>
                        <br /><br />

                        <button onClick={() => handleSaveShift(selectedShift)}>💾 Save</button>
                        <button onClick={() => handleDeleteShift(selectedShift.id)}>🗑️ Delete</button>
                        <button
                            onClick={() => {
                                setSelectedShift(null);
                                setError(null);
                            }}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "0.5rem",
                                background: "none",
                                border: "none",
                                color: "black",
                                cursor: "pointer",
                                fontSize: "1rem",
                                marginBottom: "1rem"
                            }}
                        >
                            ← Back
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default EditShift
