

import { useNavigate } from "react-router-dom";


function ShiftManager() {
    const navigate = useNavigate();


    const handleViewClick = () => {
        console.log("🟢 View Shifts button clicked");
    };
    const handlePlannedClick = () => {
        console.log("yeah")
    }

    const handleEditClick = () => {
        console.log("hey hey hey")
        navigate("/edit");
    }
    return (
        <div style={{ height: "100vh", width: "100vw", position: "relative" }}>
            {/* Title pinned top-left */}
            <div style={{
                
                textAlign: "center",
                paddingTop: " 1rem",
                fontSize: "1rem",
                fontWeight: "bold",

            }}>
                <h1>📅 Shift Manager</h1>
            </div>

            {/* Separate container: button center-left */}
            <div
                style={{
                    position: "absolute",
                    top: "50%",
                    left: "25%",
                    transform: "translateY(-50%)",
                }}
            >
                <button
                    onClick={handleViewClick}
                    style={{
                        fontSize: "2rem",
                        padding: "0.5rem 1.2rem",
                        cursor: "pointer",
                    }}
                >
                    View Shifts
                </button>
            </div>
            <div
                style={{
                    position: "absolute",
                    top: "50%",
                    right: "45%",
                    transform: "translateY(-50%)",
                }}
            >
                <button
                    onClick={handlePlannedClick}
                    style={{
                        fontSize: "2rem",
                        padding: "0.5rem 1.2rem",
                        cursor: "pointer",
                    }}
                >
                    Plan Shifts
                </button>
            </div>
            <div
                style={{
                    position: "absolute",
                    top: "50%",
                    right: "25%",
                    transform: "translateY(-50%)",
                }}
            >
                <button
                    onClick={handleEditClick}
                    style={{
                        fontSize: "2rem",
                        padding: "0.5rem 1.2rem",
                        cursor: "pointer",
                    }}
                >
                    Edit Shift
                </button>
            </div>
        </div>
    );
}

export default ShiftManager;