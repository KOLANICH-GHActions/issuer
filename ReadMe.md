isssue(Template)r [![`Unlicense`d work](https://raw.githubusercontent.com/unlicense/unlicense.org/master/static/favicon.png)](https://unlicense.org/)
=================

This is a GitHub action with 3 connected features for issues management.

1. It checks if the incoming issues match the `template` in some sense:
    * that sections contain no lines from the default template (usually present when a user hasn't cared to fill in the section);
    * that sections containing checkboxes to be set as labels contain only the checkboxes present in the original template
    * that each section has amount of checkboxes checked in the range `[min, max]`
2. It sets labels according to the checked checkboxes.
3. It automatically closes the issues if the author hasn't fixed the issues highlighted by the linter within some deadline.

Use cases
---------

Why anyone may have ever needed such a GitHub Action?

1. There are some repos which only purpose is to collect issues. Such as https://github.com/open-source-ideas/open-source-ideas/ . Using a dedicated person to assign labels is a burden, you want to allow users to do self-service. Users are enabled to assign some labels to issues from a restricted subset. It is done via a Markdown extension - checkboxes.

<details>
<summary>Like these ones.</summary>

* [ ] unchecked (source: `[ ]`)
* [x] checked (source: `[x]`)

</details>

<details>
<summary>Though there are no radio buttons.</summary>

* ( ) unchecked (source: `( )`)
* (o) checked (source: `(o)`)

</details>

A user ticks a checkbox, the bot sets the labels accordingly.

~~You also may allow a user to delete the issue wholly - just add a section with a checkbox and setup `{max: 0, min: 0, react: {delete: 60*20}}`. When a user checks it, the issue will be deleted within 20 minutes, if not unchecked.~~ (currently issue deleteon is an undocumented GH feature even support staff is not fully aware about).

2. You may want to create a checklist, that a user must fill in before creating an issue. A user must pledge that he has done the actions in the checklist in order to make the issue deserve your attention. Of course he may lie, but it is on his discretion.

Manual
------
0. Get known what you want. Answer the following questions and write them for yourself:
    * Do I want to allow users to self-manage their issues?
    * Which labels do I want to allow them self-assign?
    * Are these labels mutually exclusive in any sense?
    * What are the groups of the labels?
    * Do I want to require a user to check at least some labeles in a group?
    * How would I name complying and non-complying issue tags?
    * Do I want to close the issues not complying with the format?
    * Am I ready and in the right position to say "either do what I require you to do or f*** **f" to the people who came to my repo to help me?
    * Do I want to give a user a chance to fix that issue? How long do I aggree to wait?
    * Keeping in mind that the interval is a polling interval and on each polling a GH Action is executed, will such a cron harm GitHub anyhow? 

1. create an issue template containing all the needed sections. It should contain:
    * some sections wholly devoted to checkboxes
    * a metadata to automatically assign a label. It is `labels` key. The first label is used as a marker.
    * an `issuer` dictionary with issue-specific info according to [the JSONSchema](./IssuerGHAction/issuer.schema.json). READ IT. The most of the documentation is in the schema. If not present, the issue is ignored. If you want to override no global settings, just use `{}`.
The only checkboxes considered allowed are in the checkboxes sections of. All the other checkboxes are considered disallowed. Checkboxes removal is allowed - it decreases count of junk

2. create a `github/templater.yml` config file with global prefs. The most likely you want to customize the messages templates according to your project specifics and deadlines

3. create a workflow:
```yaml
on:
  issues:
    types: [opened, edited]
  schedule: # Needed only if you need delayed actions - closing or deleting or banning after the user have not fixed the issues
    - cron: '*/12 * * * *' # If we want 

jobs:
  lint:
    runs-on: ubuntu-latest
    name: A job to lint the issues
    steps:
      - name: clone
        run: "git clone --depth=1 https://github.com/$GITHUB_REPOSITORY ." # needed only to read the configs, probably we don't need it at all but should get it from GH cache
      - name: osi_issues
        uses: KOLANICH-GHActions/issuer@master  # it is recommended to use an own fork
        with:
          GITHUB_TOKEN: ${{secrets.GITHUB_TOKEN}}
```
