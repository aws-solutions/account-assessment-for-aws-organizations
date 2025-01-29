// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import Link from "@cloudscape-design/components/link";
import {ReactNode} from "react";
import {useNavigate} from "react-router-dom";

// wraps @cloudscape-design/components/link in a way that prevents page reloads and uses client side routing instead
export const RouterLink = (props: {
  href: string,
  children: ReactNode,
  fontSize?: 'body-s' | 'body-m' | 'heading-xs' | 'heading-s' | 'heading-m' | 'heading-l' | 'heading-xl' | 'display-l' | 'inherit',
  variant?: 'primary' | 'secondary' | 'info' | 'awsui-value-large',
  external?: boolean
}) => {
  const {
    href,
    children,
    fontSize,
    external,
    variant
  } = props;

  const navigate = useNavigate();
  return <Link
    href={href}
    external={external ?? false}
    variant={variant ?? "primary"}
    fontSize={fontSize ?? 'inherit'}
    onFollow={function (e: CustomEvent) {
      e.preventDefault(); // prevent page reload, use client side routing instead
      navigate(e.detail.href);
    }}>
    {children}
  </Link>
}