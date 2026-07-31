use std::{
    path::{Path, PathBuf},
    time::Duration,
};

use chrono::Local;
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
struct Task {
    time_left: Duration,
    name: String,
}

#[derive(Serialize, Deserialize, Debug, Default)]
enum Session {
    /// Time is ticking
    Ongoing {
        start_time: chrono::DateTime<Local>,
        duration: Duration,
    },
    #[default]
    /// No tracking
    Stopped,
}

impl Session {
    /// Side-effectful update
    fn update(self) -> Self {
        match self {
            Session::Ongoing {
                start_time,
                duration,
            } => {
                let end = start_time + duration;
                let now = chrono::offset::Local::now();
                if now < end {
                    self
                } else {
                    trigger_finish_actions();
                    Session::Stopped {}
                }
            }
            Session::Stopped => self,
        }
    }
}

#[derive(Serialize, Deserialize, Default, Debug)]
struct State {
    current_task: Option<Task>,
    current_session: Session,
}

fn read_state(state_file: &Path) -> Option<State> {
    let bytes = std::fs::read(state_file).ok()?;
    let content = str::from_utf8(&bytes).ok()?;
    serde_json::from_str(content).ok()
}

#[derive(Parser)]
struct Cli {
    #[command(subcommand)]
    command: Command,
    #[arg(short, long)]
    verbose: bool,
}

#[derive(Subcommand)]
enum Command {
    /// Start break timer
    Start {
        /// Duration in minutes
        #[arg(default_value = "0")]
        duration: u64,
    },
    /// Get break/task status
    Status {},
}

/// Trigger finishing actions.
///
/// Actions should be idempotent.
fn trigger_finish_actions() {
    std::process::Command::new("timer-action.sh")
        .arg("finish")
        .output()
        .unwrap();
}

/// Trigger starting actions.
///
/// Actions should be idempotent.
fn trigger_start_actions() {
    std::process::Command::new("timer-action.sh")
        .arg("start")
        .output()
        .unwrap();
}

fn main() {
    let state_dir =
        PathBuf::from(std::env::var("XDG_DATA_HOME").expect("XDG_DATA_HOME should be set"))
            .join("timer");
    let _ = std::fs::create_dir(&state_dir);
    let state_file = state_dir.join("timer.json");

    let mut state = read_state(&state_file).unwrap_or_default();

    let cli = Cli::parse();
    match cli.command {
        Command::Start { duration } => {
            trigger_start_actions();
            state.current_session = Session::Ongoing {
                start_time: chrono::offset::Local::now(),
                duration: Duration::from_mins(duration),
            }
        }
        Command::Status {} => {
            state.current_session = state.current_session.update();
            match state.current_session {
                Session::Ongoing {
                    start_time,
                    duration,
                } => {
                    let end = start_time + duration;
                    let now = chrono::offset::Local::now();
                    let delta = end - now;
                    let secs = delta.num_seconds();
                    println!("session: {:>02}:{:>02} remaining", secs / 60, secs % 60,);
                }
                Session::Stopped => {
                    println!("session: no tracking")
                }
            }
        }
    }

    if cli.verbose {
        println!("{state:#?}");
    }

    std::fs::write(state_file, serde_json::to_string(&state).unwrap()).unwrap();
}
