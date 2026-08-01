use clap::{Parser, Subcommand};

#[derive(Parser)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Command,
    #[arg(short, long)]
    pub verbose: bool,
}

#[derive(Subcommand)]
pub enum Command {
    /// Start break timer
    Start {
        /// Duration in minutes
        #[arg(default_value = "60")]
        duration: u32,
    },
    /// Stop break timer
    Stop {},
    /// Get break/task status
    Status {},
    /// Get short status
    Short {},
}
