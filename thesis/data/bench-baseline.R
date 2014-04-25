println <- function(...) {
	cat(..., "\n", sep="")
}

print_table <- function(label, caption, data) {
	println("\\begin{table}")
	println("  \\caption{", caption, "}")
	println("  \\label{", label, "}")
	println("\\end{table}")
}

pings <- read.csv("~/bach/thesis/data/pings.csv")

print_table("table:bench.baseline.summary",
            "Summary of baseline benchmark",
            summary_table)
        

quantile(pings$RTT, 0.25)
summary(pings)
