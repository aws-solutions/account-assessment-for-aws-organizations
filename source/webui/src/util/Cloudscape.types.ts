// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/* Types for Cloudscape Select component; unfortunately Cloudscape does not export these types, so we have to recreate them here. */
import React from "react";

export type OptionDefinition = {
  label?: string;
  disabled?: boolean;
  value?: string;
  lang?: string;
  labelTag?: string;
  description?: string;
  tags?: ReadonlyArray<string>;
  filteringTags?: ReadonlyArray<string>;
};

export type OptionGroup = {
  label?: string;
  disabled?: boolean;
  options: ReadonlyArray<OptionDefinition>;
};

export type LabelData = {
  sorted: boolean;
  descending: boolean;
  disabled: boolean;
}

export type SortingColumn<T> = {
  sortingField?: string;
  sortingComparator?: (a: T, b: T) => number;
}


export type ColumnDefinition<ItemType> = {
  id?: string;
  header: React.ReactNode;
  ariaLabel?(data: LabelData): string;
  width?: number | string;
  minWidth?: number | string;
  maxWidth?: number | string;
  isRowHeader?: boolean;
  cell(item: ItemType): React.ReactNode;
} & SortingColumn<ItemType>;

export type SortingState<T> = {
  isDescending?: boolean;
  sortingColumn: SortingColumn<T>;
}