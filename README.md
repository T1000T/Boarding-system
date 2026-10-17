# Employee Lifecycle Automation: Process Documentation

Onboarding, client moves and offboarding, automated end to end.

## 1\. Purpose and scope

The goal is to automate how people join, move between clients and leave the company. The company works with several clients, so one employee can move between clients without leaving, and the laptop can belong to either the company or the client. That fact shapes the whole design.

The exercise is built as a working web application. It simulates three target systems (Google Workspace, Slack, GitHub), a device layer, and an HR source. Everything the HR system would send is entered through a form. Everything the target systems would do is simulated by connectors that can later be replaced with real API calls.

The tool answers the four questions the brief asked for: what was done, what is still open, what failed, and who is responsible for the manual parts.

## 2\. How it works: the core idea

Every HR event becomes a list of tasks. The engine does not contain separate scripts for each situation. It holds declarative profiles and computes what to do from them.

1. **An HR event arrives.** Fields: employee, work email, role, client, manager, date, device owner, operating system, equipment, extra software, location, phone, personal email, notes.
2. **The planner builds tasks** from the event type, the role profile, the client profile and the device owner.
3. **The executor runs the tasks** one after another against the connectors, records each status and writes an audit log entry.
4. **Humans handle manual tasks** and mark them done. Failed tasks can be retried, and finished tasks can be undone.

### Profiles

* **Role profiles** (Developer, DevOps engineer, Office worker, Support agent) define GitHub teams, Slack channels, Google groups, licenses and software. An office worker gets no GitHub access and a lighter license set, while a developer gets GitHub and developer tools.
* **Client profiles** (Acme, Globex, Initech, Internal bench) define the client-specific teams, channels, and shared drives. Client software, including client VPNs, is never installed; the company VPN is the only VPN. The client list can be edited from the page.
* **Base software** (browser, Slack, password manager, company VPN) is installed for everyone on a company device.

## 3\. The three processes

### 3.1 Onboarding

Steps, in order:

1. Validate the HR record.
2. Create the Google user and add the groups from the role and client profiles.
3. Invite to Slack and add to channels.
4. Invite to the GitHub organization and teams (only if the role or client has any).
5. Assign licenses by role.
6. Device, depending on who owns it:

   * **Company device:** a manual step to prepare the hardware (due two days before the start date), then an automated software installation using the right package manager per operating system (winget, brew or apt) or send API call to MDM is available. The list is the base set plus the role's software and any extra software typed in the form.
   * **Client device:** only the company VPN is installed, and the client's own VPN is never added. A manual step to coordinate access and permissions with the client's IT, and no wipe from our side.
7. Notify the manager that everything is ready for onboarding.
8. Manual step: the onboarding meeting with the new employee, showing the start date.

### 3.2 Client move

The employee stays in the company, so this is not an offboarding followed by an onboarding. The planner computes the **difference** between the old and the new client profile and changes only that:

1. Validate the move (old client to new client).
2. Update Google groups: remove what the old client added, add what the new one needs.
3. Update Slack channels the same way.
4. Update GitHub teams the same way.
5. Device:

   * **Company device:** no client software is installed or removed; only extra software typed in the form is installed.
   * **Client device:** a manual step to clean up access on the old client's device and connect to the new client.
6. Notify the manager.

Shared access that both clients have in common is never touched, which avoids a gap where someone briefly loses access they still need.

### 3.3 Offboarding

The order is the important part. Security comes first, and nothing is deleted before the data has a new owner.

1. **Block:** suspend the Google user and revoke sessions; deactivate Slack and revoke tokens; remove the user from the GitHub organization and revoke personal access tokens and SSH keys.
2. **Transfer:** the manager takes ownership of Drive files and mail, and of repositories and open pull requests.
3. **Retain:** archive the mailbox for 30 days.
4. **Release licenses:** only after the transfer and the retention are in place, so a license is never released while data is still locked to the account.
5. **Device:** company device means a manual collection, inventory check and wipe. Client device means asking the client to revoke access, with no wipe on our side.
6. **Scheduled deletion:** the account is deleted 30 days after the departure date.

A seventh and last step, Mark employee as former, moves the employee to the former list only when it runs. Until then the employee stays active, so an offboarding can be created in advance and run on the departure date. Undoing that step makes the employee active again, and both changes are recorded in the history. The difference between blocking, transferring and releasing is deliberate: blocking removes the risk, transferring preserves the business data, and releasing is a cost saving that must wait for both.

## 4\. Running the processes: available options

### Status of every step

Pending, running, done, failed, or manual (needs a person). The page shows counters for all four states and a progress bar per event.

### Controls

* **Run all:** runs every event in the order the events were created, so an onboarding always runs before the same person's offboarding.
* **Run remaining** (per event): runs the open steps of one event.
* **Per-step controls:** Run (or Retry after a failure), Mark done for work that was done by hand, and Undo for finished steps. Undo of an automated step simulates a rollback and is logged. Steps can be used independently and in any order.
* **Retry failed:** retries only events that contain failed steps. It starts from the first failed step and continues to the next steps, and it leaves other events untouched.
* **Stop:** the step that is running finishes, but no further step starts. Stopped steps stay pending, so the next run continues from the same point.
* **Failure handling:** execution within an event is sequential, and a failure stops the later steps. This matters most in offboarding, where a failed block must never be followed by a license release.
* **Simulate random failures:** a toggle that makes some first attempts fail, so the retry and stop behavior can be shown live.
* **Collapse and expand:** every event can be collapsed to its header, which still shows a done count and a failed count. A Collapse all button switches every block at once.
* **Selective reset:** reset only task statuses, only the log, events, employees, clients, or everything. Each option needs a second click to confirm.

### Employees tab

A registry of every employee: role, where they work (client and location), manager, start date, device owner and operating system, equipment, phone, personal email, notes, and a full change history. It can be searched and filtered by active, former or all.

Details can be edited in place: role, location, manager, device, equipment, phone, personal email and notes. Each change is validated and written to the history with the old and the new value. Editing the record does not start any provisioning. Access changes go through a client move event so that they are applied and logged properly.

### Validation

* Phone numbers accept only digits, a leading plus and parentheses, with at least seven digits.
* Emails are checked against a proper address format. The work email is filled in automatically as name@develeap.com, stays editable and accepts another domain if the user changes it.
* An active employee cannot be created twice with the same email.

### Audit and history

Every run, retry, undo, manual completion, stop, reset and edit writes a line to the audit log. Each employee also carries a history of changes, including onboarding details, client moves, offboarding and manual edits.

### Storage

By default the data lives in the browser. With the small local server included (a single Python file), the app uses a predetermined `data.json` file as its database: if the file exists it is loaded, otherwise it is created on the first change. Writes are atomic, and the server listens only on the local machine because the file contains personal data.

## 5\. Design decisions and why

1. **Event in, tasks out.** One planner turns an HR event into tasks. Adding a new event type or system means adding a planner rule or a connector, not a new workflow.
2. **Declarative profiles.** Access is described by role and client, not coded per person. A move is a difference between two profiles, so there is no separate move logic.
3. **Connector layer with one interface.** Each system sits behind the same call. The current implementation is simulated, and swapping in a real API changes nothing else.
4. **Manual work is a first-class task.** Hardware, client coordination and the onboarding meeting have an owner, a due date and a status, so they are tracked with the same visibility as automated steps.
5. **Device owner as a core field.** Company and client devices need different steps. Treating the client's laptop as a manual coordination task keeps our footprint on a machine we do not control to the company VPN only.
6. **Safe ordering.** Block, then transfer, then retain, then release, then delete. A failure stops the chain at the point where continuing would be unsafe.
7. **Operator control.** Retry, undo, mark done and stop exist because real operations need to correct a run, not only start one.
8. **Idempotency by design.** Every step is meant to be safe to repeat, which is what makes retry and resume reliable.

## 6\. Assumptions

* HR is the source of truth and sends employee, role, manager, start date and equipment.
* Retention is 30 days, and the manager is the default recipient of transferred data.
* A client maps to a fixed set of teams, channels and groups.
* Roles are a fixed list; each maps to one profile.
* Offboarding blocks access on the departure date, with an option for immediate handling.
* Real SSO and a device management system are out of scope; device work is simulated with manual and automated steps.

## 7\. What is simulated and what is not

Simulated: the HR feed, all connector calls, software installation, and the random failures. Real: the planning logic, the ordering rules, the status model, retry, stop and undo behavior, validation, the audit log, the employee registry and its history, and the file-based storage.

## 8\. Known limitations and next steps

* **Dates are not enforced.** A normal offboarding is shown as scheduled for a date, but steps run when someone clicks Run. A scheduler should hold block steps until the departure date.
* **No approvals** (for example license cost or privileged access).
* **Single user, no locking, no login.**
* **Role changes made by editing an employee** do not trigger access changes. this is intentional for manually correct errors.
* **No notifications** to a chat channel when a step fails.

## 9\. From demo to production

1. **Trigger:** receive events from the HR system by webhook, with polling as a fallback and a reconciliation job that compares HR with the identity provider.
2. **Connectors:** Google Workspace Admin SDK, Slack and GitHub APIs (or SCIM where available), and an MDM such as Jamf or Intune for installations and wipes.
3. **Execution:** a workflow engine or queue with workers (for example Temporal, Celery or n8n), with retries, backoff and timers for dated actions.
4. **Data:** a real database with an append-only audit table, replacing `data.json`.
5. **Security:** least-privilege service accounts per connector, secrets in a vault, SSO and roles for the tool itself, and encryption of personal data.
6. **Governance:** approvals for sensitive access, periodic access reviews, and a dry-run mode that shows the plan without executing it.
7. **Observability:** alerts on failures, plus metrics such as time to ready on day one, failure rate per connector, and open manual tasks.

## 10\. Suggested demo script

1. Open the Automation tab and click **Load samples**. Point out the three onboardings, the client move and the offboarding in lifecycle order.
2. Show how the same planner gives a developer on a company laptop and a DevOps engineer on a client laptop different steps.
3. Turn on random failures, click **Run all**, and click **Stop** midway to show that the running step finishes and nothing new starts.
4. Click **Retry failed** and explain that it restarts only from the failed step.
5. Open the move event and show the diff between the old and new client.
6. Open the urgent offboarding and walk through block, transfer, retain, release, delete. Explain why license release comes late.
7. Use Mark done and Undo on a single step.
8. Switch to the Employees tab, open a history, edit a field, and show the new history entry.
9. Show `data.json` on disk and explain how it would become a database (only available when running as a service).

