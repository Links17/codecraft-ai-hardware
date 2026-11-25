pub mod catalog;
pub mod device;
pub mod platform;
pub mod project;
pub mod util;
pub const CONTRACT: u64 = 4;
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

pub mod skills;

pub mod firmware;
