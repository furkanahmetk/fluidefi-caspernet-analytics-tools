### Contributing

Developers must follow the [git-flow branching model](https://nvie.com/posts/a-successful-git-branching-model/) when contributing to this project and versioning must adhere to [Semantic Versioning](http://semver.org/).

#### Features

Feature branches must be forked from develop and merged back into develop.

Use the following commands to start a feature:

```
git checkout develop
git pull origin develop
git checkout -b feature/feature_name
```

Once you start pushing commits, open a PR with your branch. The title for your PR should be:

```
feature: feature_name
```

When you are ready, request review for your feature PR on Github's UI, and approval + conversation resolution is required before the branch can be merged.

Once approved, merge your branch develop in GitHub's UI, being sure to squash commits.  If you need to resolve conflicts, do the following:

```
git checkout develop
git pull origin develop
git checkout feature/feature_name
git merge --no-ff develop
```

Now you resolve the conflicts locally. And then commit the changes with:

```
git add .
git commit -m "merge develop into feature branch"
git push origin feature/feature_name
```

No you should be good to Squash and Merge in the UI.

#### Releases

Release branches must be forked from develop and merged into main and develop.

After your feature has been approved and merged into the develop branch, start the release with the following commands:

```
git checkout develop
git pull origin develop
git checkout -b release/x.y.z
```

Create a PR for your release with the title:

```
release: x.y.z
```

and description that matches the entry as it will appear in the changelog:

```
## Release x.y.z
### Added:
 - my new great feature
### Changed:
 - something that needed to be improved
```

Update the changelog and bump the version to x.y.z. Fix any bugs that may be found in the release branch.

Request review for your PR on Github. Once approved, merge your release branch into main using the UI. Make sure you squash commits.

If you have merge conflicts resolve them locally with:

```
git checkout main
git pull origin main
git checkout release/x.y.z
git merge --no-ff main
```

Now you resolve the conflicts locally. And then commit the changes with:

```
git add .
git commit -m "merge main into release branch"
git push origin release/x.y.z
```

No you should be good to Squash and Merge in the UI.

Next tag your release:

```
git checkout main
git pull origin main
git tag -a x.y.z
git push origin --tags
```

Then create a PR to merge the release branch into develop. Use the same commands above if you need to resolve conflicts.

Then merge the new tag into develop:

```
git checkout develop
git pull origin develop
git fetch --tags origin
git merge x.y.z
git push origin develop
```

Once merged, a new version of the package will be published to pyPI by admin.

#### Hotfixes

##### TODO - update the hotfix git workflow to match the steps in the workflow for a feature

Hotfix branches must be forked from main and merged into main and develop.

Start a hotfix with the following commands:

```
git checkout main
git pull origin main
git checkout -b hotfix/hotfix_name
```

Create a PR for your hotfix with the title:

```
hotfix: hotfix_name
```

Make sure to update the changelog and bump the version.  Request review when ready to merge.

Merge the hotfix into main:

```
git checkout main
git pull origin main
git merge --no-ff hotfix/hotfix_name
git tag -a x.y.z
git push origin --tags
```

Then merge the hotfix into develop:

```
git checkout develop
git pull origin develop
git merge --no-ff hotfix/hotfix_name
git branch -d hotfix/hotfix_name
```

Then merge the new tag into develop:

```
git fetch --tags origin
git merge x.y.z
git push origin develop
```

Once merged, a new version of the package will be published to pyPI by admin.
