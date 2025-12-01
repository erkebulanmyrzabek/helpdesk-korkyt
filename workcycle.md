# HelpDesk System Workcycle

This document describes the complete workflow of the HelpDesk system, from ticket creation to completion and rating.

## Roles

- **User (Teacher):** Creates tickets, confirms completion, rates work.
- **Admin:** Manages users, views statistics, can reassign tickets.
- **Helper (Helpdesk):** Accepts tickets, performs work, reports completion.

## Workflow

### 1. Ticket Creation (User/Teacher)
- **Action:** User logs in and fills out the "New Ticket" form.
- **Requirements:**
    - Title, Description, Building, Room.
    - **Photo/Video Evidence:** Mandatory.
- **System:** Creates a ticket with status `NEW`.
- **Notification:** Email sent to relevant Helpers (based on building).

### 2. Assignment & Transit (Helper)
- **Action:** Helper logs in and sees "New Tickets" for their assigned building (or all if unassigned).
- **Action:** Helper clicks "Take Ticket" (Взять в работу).
- **System:**
    - Status changes to `TRANSIT`.
    - **Timer:** A 10-minute timer starts for the Helper to arrive at the location.
    - **Restriction:** Helper cannot finish the ticket while in `TRANSIT`.

### 3. Execution (Helper)
- **Action:** Upon arrival, Helper clicks "Arrived" (Прибыл на место).
- **System:** Status changes to `IN_PROGRESS`.
- **Action:** Helper performs the work.
- **Deadline Extension:**
    - If work takes longer, Helper can add a comment.
    - **System:** Extends deadline by **7 days**.
    - **Notification:** Email sent to User about the delay.

### 4. Completion (Helper)
- **Action:** Helper clicks "Finish" (Завершить).
- **Requirements:**
    - **Photo Report:** Mandatory (upload photo of result).
    - **Resolution Report:** Mandatory (text description of what was done).
- **System:**
    - Status changes to `WAITING_APPROVE`.
    - **Notification:** Email sent to User to confirm completion.

### 5. Confirmation & Rating (User/Teacher)
- **Action:** User sees "Work Completed" card in their dashboard.
- **Action:** User reviews the Helper's photo and report.
- **Action:** User clicks "Confirm" (Подтвердить).
- **Requirements:**
    - **Rating:** 1-5 Stars.
    - **Feedback:** Optional comment.
- **System:**
    - Status changes to `CLOSED`.
    - Helper's average rating is updated.

## Constraints & Rules

- **Transit Timer:** Helpers are expected to arrive within 10 minutes.
- **Working Hours:** Tickets can only be created between 09:00 and 18:00 (Almaty Time).
- **Deadline:** Default deadline is End of Day (18:00). Extension adds 7 days.
- **Shift System:** Helpers must "Check In" to see and accept tickets. System auto-checks out at midnight.
