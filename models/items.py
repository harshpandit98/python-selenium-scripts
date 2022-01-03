from dataclasses import dataclass


@dataclass
class ProjectItem:
    """Class for keeping track of an project."""

    project_id: str
    url: str
    name: str
    registration_number: str
    promoter_name: str
    address: str
    district: str
    tehsil: str
    registered_with: str
    certificate_url: str
    ah_form_url: str
    receiving_date: str
    online_submission_date: str
    current_status: str
    next_date_of_hearing: str
    notice_dispatched: str
    notice_dispatched_on: str
    notice_tracking_id: str
    notice_dispatched_remarks: str
    view_notice: str
    initially_scrutinized_remarks: str
