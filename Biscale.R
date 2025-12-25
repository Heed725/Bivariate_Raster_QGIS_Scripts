# Biscale Palette Export Script - Wide Format
# Exports all palettes with columns: palette_name, tag, 11, 12, 13, 21, 22, 23, 31, 32, 33

library(biscale)
library(tidyverse)

# Function to export all palettes in wide format
export_all_biscale_palettes <- function(output_path = "C:/Users/User/Documents/Biscale_colors.csv",
                                        dim = 3,
                                        preview = TRUE) {
  
  # List of all available palettes
  palette_list <- c(
    "Bluegill", 
    "BlueGold", 
    "BlueOr", 
    "BlueYl",
    "Brown", 
    "Brown2",
    "DkBlue", 
    "DkBlue2",
    "DkCyan", 
    "DkCyan2",
    "DkViolet", 
    "DkViolet2",
    "GrPink", 
    "GrPink2",
    "PinkGrn", 
    "PurpleGrn", 
    "PurpleOr"
  )
  
  # Create empty list to store results
  all_palettes <- list()
  
  # Loop through each palette
  for (pal_name in palette_list) {
    
    cat("Processing:", pal_name, "\n")
    
    # Get hex values
    hex_values <- bi_pal(pal = pal_name, dim = dim, preview = FALSE)
    
    # Show preview if requested
    if (preview) {
      cat("\n")
      print(bi_pal(pal = pal_name, dim = dim, preview = TRUE))
      cat("\n")
    }
    
    # Convert position format from "1-1" to "11"
    positions <- names(hex_values)
    positions_formatted <- gsub("-", "", positions)
    
    # Create a named vector with formatted positions
    hex_vector <- setNames(as.character(hex_values), positions_formatted)
    
    # Create row data frame
    row_data <- data.frame(
      palette_name = pal_name,
      tag = pal_name,  # You can modify this if you want different tags
      stringsAsFactors = FALSE
    )
    
    # Add each position as a column
    for (pos in c("11", "21", "31", "12", "22", "32", "13", "23", "33")) {
      row_data[[pos]] <- hex_vector[pos]
    }
    
    all_palettes[[pal_name]] <- row_data
  }
  
  # Combine all rows
  combined_df <- bind_rows(all_palettes)
  
  # Reorder columns to match requested format
  combined_df <- combined_df %>%
    select(palette_name, tag, `11`, `12`, `13`, `21`, `22`, `23`, `31`, `32`, `33`)
  
  # Print the complete table
  cat("\n", rep("=", 80), "\n")
  cat("COMPLETE PALETTE TABLE\n")
  cat(rep("=", 80), "\n\n")
  print(combined_df)
  
  # Save to CSV
  write.csv(combined_df, 
            file = output_path, 
            row.names = FALSE)
  
  cat("\n✓ CSV file saved to:", output_path, "\n")
  cat("Total palettes exported:", nrow(combined_df), "\n")
  
  return(combined_df)
}

# Export all palettes
palette_data <- export_all_biscale_palettes(
  output_path = "C:/Users/User/Documents/Biscale_colors.csv",
  dim = 3,
  preview = FALSE  # Set to TRUE if you want to see visual previews
)

# View the results
print(palette_data)

# Optional: Create a prettier display
cat("\n\nPALETTE PREVIEW:\n")
cat(rep("=", 120), "\n")
for (i in 1:nrow(palette_data)) {
  cat(sprintf("%-15s | ", palette_data$palette_name[i]))
  cat(sprintf("%s %s %s | %s %s %s | %s %s %s\n",
              palette_data$`11`[i], palette_data$`12`[i], palette_data$`13`[i],
              palette_data$`21`[i], palette_data$`22`[i], palette_data$`23`[i],
              palette_data$`31`[i], palette_data$`32`[i], palette_data$`33`[i]))
}
cat(rep("=", 120), "\n")

# Alternative: Export with additional metadata
export_palettes_with_metadata <- function(output_path = "C:/Users/User/Documents/Biscale_colors_metadata.csv",
                                          dim = 3) {
  
  palette_list <- c(
    "Bluegill", "BlueGold", "BlueOr", "BlueYl",
    "Brown", "Brown2",
    "DkBlue", "DkBlue2",
    "DkCyan", "DkCyan2",
    "DkViolet", "DkViolet2",
    "GrPink", "GrPink2",
    "PinkGrn", "PurpleGrn", "PurpleOr"
  )
  
  # Define palette categories/tags
  palette_tags <- c(
    "Bluegill" = "Blue-Green",
    "BlueGold" = "Blue-Gold",
    "BlueOr" = "Blue-Orange",
    "BlueYl" = "Blue-Yellow",
    "Brown" = "Brown (Legacy)",
    "Brown2" = "Brown (Extended)",
    "DkBlue" = "Dark Blue (Legacy)",
    "DkBlue2" = "Dark Blue (Extended)",
    "DkCyan" = "Dark Cyan (Legacy)",
    "DkCyan2" = "Dark Cyan (Extended)",
    "DkViolet" = "Dark Violet (Legacy)",
    "DkViolet2" = "Dark Violet (Extended)",
    "GrPink" = "Gray-Pink (Legacy)",
    "GrPink2" = "Gray-Pink (Extended)",
    "PinkGrn" = "Pink-Green",
    "PurpleGrn" = "Purple-Green",
    "PurpleOr" = "Purple-Orange"
  )
  
  all_palettes <- list()
  
  for (pal_name in palette_list) {
    hex_values <- bi_pal(pal = pal_name, dim = dim, preview = FALSE)
    positions_formatted <- gsub("-", "", names(hex_values))
    hex_vector <- setNames(as.character(hex_values), positions_formatted)
    
    row_data <- data.frame(
      palette_name = pal_name,
      tag = palette_tags[pal_name],
      stringsAsFactors = FALSE
    )
    
    for (pos in c("11", "21", "31", "12", "22", "32", "13", "23", "33")) {
      row_data[[pos]] <- hex_vector[pos]
    }
    
    all_palettes[[pal_name]] <- row_data
  }
  
  combined_df <- bind_rows(all_palettes)
  combined_df <- combined_df %>%
    select(palette_name, tag, `11`, `12`, `13`, `21`, `22`, `23`, `31`, `32`, `33`)
  
  write.csv(combined_df, file = output_path, row.names = FALSE)
  
  cat("✓ CSV with metadata saved to:", output_path, "\n")
  return(combined_df)
}

# Uncomment to export with descriptive tags:
# palette_data_metadata <- export_palettes_with_metadata()

# Function to export a subset of palettes
export_selected_palettes <- function(palette_names,
                                     output_path = "C:/Users/User/Documents/Biscale_colors_selected.csv",
                                     dim = 3) {
  
  all_palettes <- list()
  
  for (pal_name in palette_names) {
    hex_values <- bi_pal(pal = pal_name, dim = dim, preview = FALSE)
    positions_formatted <- gsub("-", "", names(hex_values))
    hex_vector <- setNames(as.character(hex_values), positions_formatted)
    
    row_data <- data.frame(
      palette_name = pal_name,
      tag = pal_name,
      stringsAsFactors = FALSE
    )
    
    for (pos in c("11", "21", "31", "12", "22", "32", "13", "23", "33")) {
      row_data[[pos]] <- hex_vector[pos]
    }
    
    all_palettes[[pal_name]] <- row_data
  }
  
  combined_df <- bind_rows(all_palettes)
  combined_df <- combined_df %>%
    select(palette_name, tag, `11`, `12`, `13`, `21`, `22`, `23`, `31`, `32`, `33`)
  
  write.csv(combined_df, file = output_path, row.names = FALSE)
  
  cat("✓ Selected palettes saved to:", output_path, "\n")
  return(combined_df)
}

# Example: Export only specific palettes
# selected <- export_selected_palettes(
#   palette_names = c("GrPink", "DkViolet", "BlueYl"),
#   output_path = "C:/Users/User/Documents/Biscale_colors_selected.csv"
# )

cat("\n\n✓ Script completed successfully!\n")
cat("Main output file: C:/Users/User/Documents/Biscale_colors.csv\n")
