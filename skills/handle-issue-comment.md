# Goal

Reply to a comment on a pull request appropriately, using the codebase, pull request description and comment history as context.

# Steps
* Get all the comments to build context using `gh issue view --comments`.
* Pull the codebase for the repository using `gh repo clone`.
* Reply to the comment appropriately, using the codebase, issue description and comment history as context.
