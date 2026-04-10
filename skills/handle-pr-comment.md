# Goal

Reply to a comment on a pull request appropriately, using the codebase, pull request description and comment history as context.

# Steps
* Get all the prior comments to build context using `gh pr view --comments`.
* Pull the codebase for the repository using `gh repo clone`.
* Determine whether the feedback (the comment) is appropriate and actionable.
	* If it is appropriate and actionable, implement the requested changes in the codebase.
	* If it is not appropriate or actionable, respond to the comment explaining why the change will not be made.
		* When addressing the comments, first display its content, then explain your reasoning for accepting or rejecting it, then let me approve or reject your decision
			* If the decision is approved, either make the change or respond to the comment as appropriate.

If changes are to be made, make the changes, then commit and push the changes to the PR branch.
