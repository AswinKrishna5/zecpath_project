ALLOWED_TRANSITIONS = {
    "APPLIED": ["SHORTLISTED", "REJECTED"],
    "SHORTLISTED": ["INTERVIEW", "REJECTED"],
    "INTERVIEW": ["SELECTED", "REJECTED"],
    "SELECTED": [],
    "REJECTED": [],
}

def is_valid_transition(current_status,new_status):
    return new_status in ALLOWED_TRANSITIONS.get(current_status,[])
