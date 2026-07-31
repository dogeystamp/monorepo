use std::{
    path::{Path, PathBuf},
    time::Duration,
};

use chrono::{Local, TimeDelta};
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

/// Computed [`Session`] information.
enum SessionStatus {
    Ongoing {
        duration: Duration,
        start_time: chrono::DateTime<Local>,
        end_time: chrono::DateTime<Local>,
        until_end: TimeDelta,
    },
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

    fn status(&self) -> SessionStatus {
        match &self {
            Session::Ongoing {
                start_time,
                duration,
            } => {
                let end_time = *start_time + *duration;
                let now = chrono::offset::Local::now();
                SessionStatus::Ongoing {
                    duration: *duration,
                    start_time: *start_time,
                    end_time,
                    until_end: end_time - now,
                }
            }
            Session::Stopped => SessionStatus::Stopped,
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
        #[arg(default_value = "60")]
        duration: u64,
    },
    /// Get break/task status
    Status {},
    /// Get short status
    Short {},
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
    let state_file = if cfg!(not(debug_assertions)) {
        state_dir.join("timer.json")
    } else {
        state_dir.join("timer-staging.json")
    };

    let mut state = read_state(&state_file).unwrap_or_default();
    state.current_session = state.current_session.update();

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
            println!("SESSION");
            match state.current_session.status() {
                SessionStatus::Ongoing {
                    until_end,
                    duration,
                    start_time,
                    end_time,
                } => {
                    let secs = until_end.num_seconds();
                    println!(
                        "{} -> {} ({}m)",
                        start_time.format("%H:%m"),
                        end_time.format("%H:%m"),
                        duration.as_secs() / 60
                    );
                    println!("{:>02}:{:>02} remaining", secs / 60, secs % 60,);
                }
                SessionStatus::Stopped => {
                    println!("no tracking")
                }
            }
        }
        Command::Short {} => match state.current_session.status() {
            SessionStatus::Ongoing { until_end, .. } => {
                let secs = until_end.num_seconds();
                println!("{:>02}:{:>02}", secs / 60, secs % 60,);
            }
            SessionStatus::Stopped => println!("--:--"),
        },
    }

    if cli.verbose {
        println!("{state:#?}");
    }

    std::fs::write(state_file, serde_json::to_string(&state).unwrap()).unwrap();
}
