"use strict";
/*
GH Actions Node actions don't support modules
import {env} from "process";
import {execSync} from "child_process";
import {join} from "path";
*/

const join = require("path").join;
const execSync = require("child_process").execSync;
const env = require("process").env;


//console.log(process.env);
// /home/runner/work/_actions/KOLANICH/OSIIssues.py/master/

const setupCommand = "bash ./setup.sh";
const runCommand = "sh " + join(__dirname, "run.sh")

execSync(setupCommand, {"cwd":__dirname, "stdio":"inherit"});
//execSync(runCommand, {"cwd": env.GITHUB_WORKSPACE, "stdio":"inherit"});
execSync(runCommand, {"stdio":"inherit"});







